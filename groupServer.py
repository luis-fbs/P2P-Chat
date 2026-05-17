from socket import *
import pickle


import constants
from group import Group
from peer import Peer


class GroupServer:
    def __init__(self, port = constants.GROUP_PORT):
        self.port = port
        self.groups = []

        self.serverSock = socket(AF_INET, SOCK_STREAM)
        self.serverSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.serverSock.bind(('0.0.0.0', self.port))
        self.serverSock.listen()

        self.handlers = {
            "register_group": self.handle_group_register,
            "unregister_group": self.handle_group_unregister,
            "register_peer": self.handle_peer_register,
            "unregister_peer": self.handle_peer_unregister,
            "list_groups": self.handle_group_list,
            "list_peers": self.handle_peer_list
        }

   # main
    def serve(self):
        while True:
            conn, addr = self.serverSock.accept()
            try:
                self.handle_connection(conn)
            finally:
                conn.close()

    def handle_connection(self, conn):
        try:
            msg = conn.recv(2048)
            if not msg:
                return

            request = pickle.loads(msg)
            operation = request.get("operation")

            handler = self.handlers.get(operation, self.handle_unknown)
            handler(request, conn)

        except Exception as e:
            print("Error handling connection:", e)

    # Operations
    def handle_group_register(self, request, conn):
        group = request.get("group")
        message = ""
        if group not in self.groups:
            self.groups.append(group)
            message = f"Group {group.name} registered."

        response = {
            "message": message or "Group already registered.",
        }
        conn.send(pickle.dumps(response))


    def handle_group_unregister(self, request, conn):
        group = request.get("group")
        message = ""
        if group in self.groups:
            self.groups.remove(group)
            message = f"Group {group.name} unregistered."

        response = {
            "message": message or "Group doesn't exist.",
        }
        conn.send(pickle.dumps(response))

    def handle_peer_register(self, request, conn):
        group = request.get("group")
        peer = request.get("peer")
        try:
            g_index = self.groups.index(group)
            self.groups[g_index].add_peer(peer)
            message = f"Peer {peer.user.nickname} ({peer.ip}:{peer.port}) registered."

        except ValueError:
            message = f"Group {group.name} not registered."

        finally:
            response = {
                "message": message
            }
            conn.send(pickle.dumps(response))

    def handle_peer_unregister(self, request, conn):
        group = request.get("group")
        peer = request.get("peer")
        try:
            g_index = self.groups.index(group)
            self.groups[g_index].remove_peer(peer)
            message = f"Peer {peer} unregistered."

        except ValueError:
            message = f"Group {group.name} not registered."

        finally:
            response = {
                "message": message
            }
            conn.send(pickle.dumps(response))

    def handle_group_list(self, request, conn):
        response = {"message": [group.name for group in self.groups]}
        conn.send(pickle.dumps(response))

    def handle_peer_list(self, request, conn):
        group = request.get("group")
        message = ""
        try:
            g_index = self.groups.index(group)
            peer_list = self.groups[g_index].get_peers()
            message = [(peer.user.nickname, peer.ip, peer.port) for peer in peer_list]

        except ValueError:
            message = f"Group {group.name} not registered."

        finally:
            response = {
                "message": message
            }
            conn.send(pickle.dumps(response))

    def handle_unknown(self, request, conn):
        response = {"message": "Unknown operation"}
        conn.send(pickle.dumps(response))

# Run
GroupServer().serve()
