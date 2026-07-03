import zmq

import constants
from group import Group
from net import get_public_ip


class GroupServer:
    def __init__(self, ns_address=constants.NS_ADDRESS, port=constants.GS_PORT):
        self.groups = {}
        self.ns_address = ns_address
        self.port = port
        self.ip = get_public_ip()
        self.address = f"tcp://{self.ip}:{self.port}"

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{self.port}")

        self.handlers = {
            "register_group": self.register_group,
            "unregister_group": self.unregister_group,
            "list_groups": self.list_groups,
            "register_peer": self.register_peer,
            "unregister_peer": self.unregister_peer,
            "list_peers": self.list_peers,
        }

        self.register_in_name_service()

    def register_in_name_service(self):
        sock = self.context.socket(zmq.REQ)
        sock.setsockopt(zmq.LINGER, 0)
        sock.setsockopt(zmq.RCVTIMEO, 3000)
        sock.connect(self.ns_address)
        try:
            for request in (
                {"operation": "unbind", "name": constants.GS_NAME},
                {"operation": "bind", "name": constants.GS_NAME, "address": self.address},
                {"operation": "register", "name": constants.GS_NAME, "type": "service"},
            ):
                sock.send_json(request)
                sock.recv_json()
        finally:
            sock.close()
        print(f"GroupServer registered as '{constants.GS_NAME}' at {self.address}")

    def serve(self):
        while True:
            request = self.socket.recv_json()
            operation = request.get("operation")
            handler = self.handlers.get(operation, self.handle_unknown)
            self.socket.send_json(handler(request))

    def _ok(self, message, value=None):
        return {"status": "ok", "message": message, "return": value}

    def _error(self, message):
        return {"status": "error", "message": message}

    def register_group(self, request):
        name = request.get("group")
        if name in self.groups:
            return self._ok(f"Group '{name}' already exists.")
        self.groups[name] = Group(name)
        return self._ok(f"Group '{name}' registered.")

    def unregister_group(self, request):
        name = request.get("group")
        if name not in self.groups:
            return self._error(f"Group '{name}' not found.")
        del self.groups[name]
        return self._ok(f"Group '{name}' unregistered.")

    def list_groups(self, request):
        return self._ok("", list(self.groups.keys()))

    def register_peer(self, request):
        name, peer = request.get("group"), request.get("peer")
        if name not in self.groups:
            return self._error(f"Group '{name}' not found.")
        self.groups[name].add_peer(peer)
        return self._ok(f"Peer '{peer}' joined '{name}'.")

    def unregister_peer(self, request):
        name, peer = request.get("group"), request.get("peer")
        if name not in self.groups:
            return self._error(f"Group '{name}' not found.")
        self.groups[name].remove_peer(peer)
        return self._ok(f"Peer '{peer}' left '{name}'.")

    def list_peers(self, request):
        name = request.get("group")
        if name not in self.groups:
            return self._error(f"Group '{name}' not found.")
        return self._ok("", self.groups[name].get_peers())

    def handle_unknown(self, request):
        return self._error("Unknown operation.")


if __name__ == "__main__":
    GroupServer().serve()
