class Group:
    def __init__(self, name):
        self.name = name
        self.members = []

    def __eq__(self, other):
        return self.name == other.name

    def add_peer(self, peer):
        if peer not in self.members:
            self.members.append(peer)

    def remove_peer(self, peer):
        if peer in self.members:
            self.members.remove(peer)

    def get_peers(self):
        return self.members