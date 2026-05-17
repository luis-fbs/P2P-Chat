import pickle
import threading
from socket import *

import requests

import constants
from group import Group
from user import User


class Peer:
    def __init__(self, user, port = constants.PEER_PORT):
        self.user = user
        self.port = port
        self.ip = self.get_public_ip()

    def __eq__(self, other):
        return self.user == other.user and self.port == other.port and self.ip == other.ip

    def get_public_ip(self):
        return requests.get('https://api.ipify.org').content.decode('utf8')

    def send_request(self, request):
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect((constants.GROUP_IP, constants.GROUP_PORT))
            s.send(pickle.dumps(request))
            response = s.recv(4096)
            return pickle.loads(response)

    def register_group(self, group):
        request = {
            "operation": "register_group",
            "group": group
        }
        return self.send_request(request)

    def unregister_group(self, group):
        request = {
            "operation": "unregister_group",
            "group": group
        }
        return self.send_request(request)

    def register_peer(self, group):
        request = {
            "operation": "register_peer",
            "group": group,
            "peer": self
        }
        return self.send_request(request)

    def unregister_peer(self, group):
        request = {
            "operation": "unregister_peer",
            "group": group,
            "peer": self
        }
        return self.send_request(request)

    def list_groups(self):
        request = {
            "operation": "list_groups"
        }
        return self.send_request(request)

    def list_peers(self, group):
        request = {
            "operation": "list_peers",
            "group": group
        }
        return self.send_request(request)

    # chat
    def send_message(self, address, message):
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect(address)
            s.send(pickle.dumps({"content": message, "user": self.user.nickname}))

    def broadcast_message(self, addresses, message):
        for address in addresses:
            self.send_message(address, message)

#ToDo: For V2, this function will be delegated to a chat class
    def listen_group(self):
        def listener():
            with socket(AF_INET, SOCK_STREAM) as s:
                s.bind(("0.0.0.0", self.port))
                s.listen()
                while True:
                    conn, addr = s.accept()
                    with conn:
                        data = conn.recv(4096)
                        if data:
                            message = pickle.loads(data)
                            if message["content"] == f"/bye {self.user.nickname}":
                                break
                            print(f"\n[{message.get('user')}] {message.get('content')}\n")
        threading.Thread(target=listener, ).start()
