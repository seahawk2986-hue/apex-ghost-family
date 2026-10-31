"""
TRAINING OBJECTIVE #2 (human-assigned): implement a MinStack in this file.

Implement a MinStack class satisfying:
  - push(x), pop() (pop returns the popped value), top(), and get_min()
  - get_min() is O(1) time and O(n) space at most
  - pop/top/get_min on an empty stack raise IndexError with clear messages
  - handle int and float values

Current state: intentionally incomplete - Apex, apply the full pipeline:
spec-first tests from this objective, then implement to satisfy them.
"""

class MinStack:
    """A stack with O(1) minimum retrieval."""

    def __init__(self):
        self._stack = []

    # TODO: implement push, pop, top, get_min per the objective.
    def push(self, x):
        raise NotImplementedError("training objective - implement me")