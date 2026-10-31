"""
TRAINING OBJECTIVE (human-assigned, 2026-10-31):

Implement a Calculator class in this file so that it satisfies:
  - methods: add(a, b), subtract(a, b), multiply(a, b), divide(a, b)
  - divide raises ZeroDivisionError on zero divisor (do not swallow it)
  - every operation is recorded in self.history as a string like "2 + 3 = 5"
  - a clear() method empties history
  - all operations must work for ints and floats

Current state: intentionally incomplete - Apex, apply your full pipeline:
spec-first tests derived from this objective, then implement to satisfy them.
"""

class Calculator:
    """A simple arithmetic calculator with operation history."""

    def __init__(self):
        self.history = []

    # TODO: implement add, subtract, multiply, divide, clear per the objective.
    # TRAINING NOTE: division by zero must raise ZeroDivisionError with a clear message.
    def add(self, a, b):
        raise NotImplementedError("training objective - implement me")

    def subtract(self, a, b):
        raise NotImplementedError("training objective - implement me")

    def multiply(self, a, b):
        raise NotImplementedError("training objective - implement me")

    def divide(self, a, b):
        raise NotImplementedError("training objective - implement me")


if __name__ == "__main__":
    c = Calculator()
    print(c.add(2, 3))
    print(c.divide(10, 2))