import zmq


class NameServer:
    def __init__(self):
        self.bindings = {}
        self.types = {}

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://0.0.0.0:5678")

        self.handlers = {
            "bind": self.bind,
            "lookup": self.lookup,
            "unbind": self.unbind,
            "register": self.register,
            "unregister": self.unregister,
            "discover": self.discover,
        }

    # main
    def serve(self):
        while True:
            request = self.socket.recv_json()
            operation = request.get("operation")
            handler = self.handlers.get(operation, self.handle_unknown)
            response = handler(request)
            self.socket.send_json(response)

    # returns
    def _ok(self, message, value):
        return {"status": "ok", "message": message, "return": value}

    def _error(self, message):
        return {"status": "error", "message": message}

    # Operations
    def bind(self, request):
        name, address = request["name"], request["address"]
        if name in self.bindings:
            return self._error(f"Name '{name}' already bound.")
        self.bindings[name] = address
        return self._ok(f"'{name}' bound to {address}.", None)


if __name__ == "__main__":
    server = NameServer()
    server.serve()