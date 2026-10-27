class MinHeap:
    def __init__(self):
        self.items = []

    def push(self, value):
        self.items.append(value)
        index = len(self.items) - 1

        while index > 0:
            parent = (index - 1) // 2
            if self.items[parent] <= self.items[index]:
                break

            temp = self.items[parent]
            self.items[parent] = self.items[index]
            self.items[index] = temp
            index = parent

    def pop(self):
        if self.is_empty():
            raise IndexError("The heap is empty")

        smallest = self.items[0]
        last = self.items.pop()
        if self.is_empty():
            return smallest

        self.items[0] = last
        index = 0

        while index * 2 + 1 < len(self.items):
            left = index * 2 + 1
            right = left + 1
            smaller = left

            if right < len(self.items):
                if self.items[right] < self.items[left]:
                    smaller = right

            if self.items[index] <= self.items[smaller]:
                break

            temp = self.items[index]
            self.items[index] = self.items[smaller]
            self.items[smaller] = temp
            index = smaller

        return smallest

    def peek(self):
        if self.is_empty():
            raise IndexError("The heap is empty")
        return self.items[0]

    def size(self):
        return len(self.items)

    def is_empty(self):
        return len(self.items) == 0
