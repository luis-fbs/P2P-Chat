class User():
    def __init__(self, name, nickname):
        self.name = name
        self.nickname = nickname

    def __eq__(self, other):
        return self.nickname == other.nickname