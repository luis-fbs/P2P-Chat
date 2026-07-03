import threading
import time

import zmq

import constants
from net import get_public_ip
from vector_clock import VectorClock


class Peer:
    def __init__(self, user, group=constants.DEFAULT_GROUP,
                 ns_address=constants.NS_ADDRESS, host=None,
                 port=constants.PEER_PORT):
        self.user = user
        self.name = user.nickname
        self.group = group
        self.ns_address = ns_address
        self.gs_address = None
        self.port = port
        self.ip = host or self.get_public_ip()
        self.address = f"tcp://{self.ip}:{self.port}"

        self.context = zmq.Context.instance()

        self.pub = self.context.socket(zmq.PUB)
        self.pub.bind(f"tcp://*:{self.port}")

        self.sub = self.context.socket(zmq.SUB)
        self.sub.setsockopt_string(zmq.SUBSCRIBE, "")

        self.clock = VectorClock(self.name)
        self.buffer = []
        self.lock = threading.Lock()

        self.connected = set()
        self.on_deliver = self._default_deliver

        self.running = False
        self.listener = None

    def __eq__(self, other):
        return self.name == other.name

    def get_public_ip(self):
        return get_public_ip()

    def send_request(self, request, address=None):
        address = address or self.ns_address
        sock = self.context.socket(zmq.REQ)
        sock.setsockopt(zmq.LINGER, 0)
        sock.setsockopt(zmq.RCVTIMEO, 3000)
        sock.connect(address)
        try:
            sock.send_json(request)
            return sock.recv_json()
        finally:
            sock.close()

    def bind_name(self):
        self.send_request({"operation": "unbind", "name": self.name})
        self.send_request({
            "operation": "bind",
            "name": self.name,
            "address": self.address,
        })
        return self.send_request({
            "operation": "register",
            "name": self.name,
            "type": "peer",
        })

    def unbind_name(self):
        return self.send_request({"operation": "unbind", "name": self.name})

    def lookup(self, name):
        response = self.send_request({"operation": "lookup", "name": name})
        if response.get("status") == "ok":
            return response.get("return")
        return None

    def resolve_group_server(self, retries=10, delay=0.5):
        for _ in range(retries):
            address = self.lookup(constants.GS_NAME)
            if address:
                self.gs_address = address
                return address
            time.sleep(delay)
        raise RuntimeError("Group server not registered in the name service.")

    def register_group(self, group=None):
        group = group or self.group
        return self.send_request(
            {"operation": "register_group", "group": group}, self.gs_address)

    def unregister_group(self, group=None):
        group = group or self.group
        return self.send_request(
            {"operation": "unregister_group", "group": group}, self.gs_address)

    def list_groups(self):
        response = self.send_request({"operation": "list_groups"}, self.gs_address)
        return response.get("return") or []

    def register_peer(self, group=None):
        group = group or self.group
        return self.send_request(
            {"operation": "register_peer", "group": group, "peer": self.name},
            self.gs_address)

    def unregister_peer(self, group=None):
        group = group or self.group
        return self.send_request(
            {"operation": "unregister_peer", "group": group, "peer": self.name},
            self.gs_address)

    def list_peers(self, group=None):
        group = group or self.group
        response = self.send_request(
            {"operation": "list_peers", "group": group}, self.gs_address)
        return response.get("return") or []

    def send_message(self, content):
        with self.lock:
            self.clock.increment()
            stamp = self.clock.to_dict()
        self.pub.send_json({
            "type": "message",
            "sender": self.name,
            "content": content,
            "clock": stamp,
        })

    def listen_group(self):
        self.running = True
        self.listener = threading.Thread(target=self._listener_loop, daemon=True)
        self.listener.start()

    def leave(self):
        self.running = False
        self.unregister_peer()
        self.unbind_name()
        if self.listener:
            self.listener.join(timeout=2)

    def _listener_loop(self):
        poller = zmq.Poller()
        poller.register(self.sub, zmq.POLLIN)
        last_discovery = 0.0

        while self.running:
            now = time.time()
            if now - last_discovery >= constants.DISCOVERY_INTERVAL:
                self._connect_new_peers()
                last_discovery = now

            events = dict(poller.poll(timeout=500))
            if self.sub in events:
                message = self.sub.recv_json()
                if message.get("type") == "message":
                        self._receive(message)

    def _connect_new_peers(self):
        for name in self.list_peers():
            if name == self.name:
                continue
            address = self.lookup(name)
            if not address or address in self.connected:
                continue
            self.sub.connect(address)
            self.connected.add(address)

    def _receive(self, message):
        with self.lock:
            if not self.clock.is_deliverable(message["sender"], message["clock"]):
                message["_buffered"] = True
                print(f"[HELD] {message['sender']}: {message['content']!r} - waiting for {self._missing_dependencies(message)}")
            self.buffer.append(message)
            self._drain_buffer()

    def _drain_buffer(self):
        progressed = True
        while progressed:
            progressed = False
            for message in list(self.buffer):
                if self.clock.is_deliverable(message["sender"], message["clock"]):
                    self.buffer.remove(message)
                    self.clock.update_on_deliver(message["sender"])
                    self.on_deliver(message)
                    if message.get("_buffered"):
                        print(" -> delivered from buffer")
                    progressed = True

    def _missing_dependencies(self, message):
        sender, clock = message["sender"], message["clock"]
        missing = []
        expected = self.clock.get(sender) + 1
        if clock.get(sender, 0) != expected:
            missing.append(f"{sender}:{expected} (have {sender}:{self.clock.get(sender)})")
        for node, timestamp in clock.items():
            if node != sender and timestamp > self.clock.get(node):
                missing.append(f"{node}:{timestamp} (have {node}:{self.clock.get(node)})")
        return ", ".join(missing)

    def _default_deliver(self, message):
        print(f"[{self.clock}] {message['sender']}: {message['content']}")
