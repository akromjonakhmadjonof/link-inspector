class TreeNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None


class BinarySearchTree:
    def __init__(self):
        self.root = None
        self.count = 0

    def insert(self, value):
        if self.root is None:
            self.root = TreeNode(value)
            self.count += 1
            return

        current = self.root
        while current is not None:
            if value == current.value:
                return

            if value < current.value:
                if current.left is None:
                    current.left = TreeNode(value)
                    self.count += 1
                    return
                current = current.left
            else:
                if current.right is None:
                    current.right = TreeNode(value)
                    self.count += 1
                    return
                current = current.right

    def contains(self, value):
        current = self.root

        while current is not None:
            if value == current.value:
                return True
            if value < current.value:
                current = current.left
            else:
                current = current.right

        return False

    def remove(self, value):
        self.root = self._remove(self.root, value)

    def _remove(self, node, value):
        if node is None:
            raise KeyError(value)

        if value < node.value:
            node.left = self._remove(node.left, value)
        elif value > node.value:
            node.right = self._remove(node.right, value)
        else:
            if node.left is None:
                self.count -= 1
                return node.right
            if node.right is None:
                self.count -= 1
                return node.left

            smallest = node.right
            while smallest.left is not None:
                smallest = smallest.left

            node.value = smallest.value
            node.right = self._remove(node.right, smallest.value)

        return node

    def to_list(self):
        values = []
        self._inorder(self.root, values)
        return values

    def _inorder(self, node, values):
        if node is not None:
            self._inorder(node.left, values)
            values.append(node.value)
            self._inorder(node.right, values)

    def size(self):
        return self.count

    def is_empty(self):
        return self.count == 0
