class VectorClock:
    def __init__(self, node_id, clock=None):
        self.node_id = node_id
        self.clock = dict(clock) if clock else {}

    def get(self, node):
        return self.clock.get(node, 0)

    def increment(self):
        self.clock[self.node_id] = self.get(self.node_id) + 1
        return self

    def to_dict(self):
        return dict(self.clock)

    def copy(self):
        return VectorClock(self.node_id, self.clock)

    def is_deliverable(self, sender, sender_clock):
        if sender_clock.get(sender, 0) != self.get(sender) + 1:
            return False
        for node, timestamp in sender_clock.items():
            if node == sender:
                continue
            if timestamp > self.get(node):
                return False
        return True

    def update_on_deliver(self, sender):
        self.clock[sender] = self.get(sender) + 1

    def __str__(self):
        items = ", ".join(f"{name}:{value}" for name, value in sorted(self.clock.items()))
        return "{" + items + "}"

    def __repr__(self):
        return f"VectorClock({self.node_id!r}, {self.clock!r})"
