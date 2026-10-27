class HashMap:
    def __init__(self, capacity=8):
        if capacity < 1:
            raise ValueError("Capacity must be positive")

        self.buckets = []
        for i in range(capacity):
            self.buckets.append([])
        self.count = 0

    def put(self, key, value):
        index = hash(key) % len(self.buckets)
        bucket = self.buckets[index]

        for pair in bucket:
            if pair[0] == key:
                pair[1] = value
                return

        bucket.append([key, value])
        self.count += 1

        if self.count > len(self.buckets) * 0.75:
            self._resize()

    def get(self, key, default=None):
        index = hash(key) % len(self.buckets)

        for pair in self.buckets[index]:
            if pair[0] == key:
                return pair[1]

        return default

    def contains(self, key):
        index = hash(key) % len(self.buckets)

        for pair in self.buckets[index]:
            if pair[0] == key:
                return True

        return False

    def remove(self, key):
        index = hash(key) % len(self.buckets)
        bucket = self.buckets[index]

        for i in range(len(bucket)):
            if bucket[i][0] == key:
                pair = bucket.pop(i)
                self.count -= 1
                return pair[1]

        raise KeyError(key)

    def _resize(self):
        old_buckets = self.buckets
        self.buckets = []

        for i in range(len(old_buckets) * 2):
            self.buckets.append([])

        self.count = 0
        for bucket in old_buckets:
            for key, value in bucket:
                self.put(key, value)

    def keys(self):
        keys = []
        for bucket in self.buckets:
            for key, value in bucket:
                keys.append(key)
        return keys

    def items(self):
        items = []
        for bucket in self.buckets:
            for key, value in bucket:
                items.append((key, value))
        return items

    def size(self):
        return self.count

    def is_empty(self):
        return self.count == 0
