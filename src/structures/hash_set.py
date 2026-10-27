from .hash_map import HashMap


class HashSet:
    def __init__(self):
        self.map = HashMap()

    def add(self, value):
        self.map.put(value, True)

    def contains(self, value):
        return self.map.contains(value)

    def remove(self, value):
        self.map.remove(value)

    def discard(self, value):
        if self.contains(value):
            self.remove(value)

    def values(self):
        return self.map.keys()

    def size(self):
        return self.map.size()

    def is_empty(self):
        return self.map.is_empty()
