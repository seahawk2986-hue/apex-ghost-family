class Calculator:
    """A simple arithmetic calculator with operation history."""

    def __init__(self):
        self.history = []

    # TODO: implement add, subtract, multiply, divide, clear per the objective.
    # TRAINING NOTE: division by zero must raise ZeroDivisionError with a clear message.
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def subtract(self, a, b):
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result

    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result

    def clear(self):
        self.history.clear()

if __name__ == "__main__":
    c = Calculator()
    print(c.add(2, 3))
    print(c.divide(10, 2))