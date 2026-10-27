from .linked_list import LinkedList


class Queue:
    def __init__(self):
        self.linked_list = LinkedList()

    def enqueue(self, value):
        self.linked_list.append(value)

    def dequeue(self):
        if self.is_empty():
            raise IndexError("The queue is empty")
        return self.linked_list.pop_front()

    def peek(self):
        if self.is_empty():
            raise IndexError("The queue is empty")
        return self.linked_list.peek()

    def is_empty(self):
        return self.linked_list.is_empty()

    def size(self):
        return self.linked_list.size()
