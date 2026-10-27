class Node:
    def __init__(self, value):
        self.value = value
        self.next = None


class LinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.count = 0

    def append(self, value):
        new_node = Node(value)

        if self.head is None:
            self.head = new_node
        else:
            self.tail.next = new_node

        self.tail = new_node
        self.count += 1

    def prepend(self, value):
        new_node = Node(value)
        new_node.next = self.head
        self.head = new_node

        if self.tail is None:
            self.tail = new_node

        self.count += 1

    def pop_front(self):
        if self.is_empty():
            raise IndexError("The linked list is empty")

        value = self.head.value
        self.head = self.head.next
        self.count -= 1

        if self.head is None:
            self.tail = None

        return value

    def peek(self):
        if self.is_empty():
            raise IndexError("The linked list is empty")
        return self.head.value

    def is_empty(self):
        return self.count == 0

    def size(self):
        return self.count

    def to_list(self):
        values = []
        current = self.head

        while current is not None:
            values.append(current.value)
            current = current.next

        return values
