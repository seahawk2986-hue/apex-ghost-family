class MinStack:
    """A stack with O(1) minimum retrieval."""

    def __init__(self):
        self._stack = []
        self._min_stack = []

    def push(self, x):
        if not self._stack or x <= self._min_stack[-1]:
            self._min_stack.append(x)
        self._stack.append(x)

    def pop(self):
        if not self._stack:
            raise IndexError("pop from empty stack")
        if self._stack[-1] == self._min_stack[-1]:
            self._min_stack.pop()
        return self._stack.pop()

    def top(self):
        if not self._stack:
            raise IndexError("top from empty stack")
        return self._stack[-1]

    def get_min(self):
        if not self._min_stack:
            raise IndexError("get_min from empty stack")
        return self._min_stack[-1]