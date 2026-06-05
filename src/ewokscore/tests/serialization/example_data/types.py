class CustomType:
    def __init__(self, value):
        self._value = value

    def __eq__(self, value):
        return isinstance(value, CustomType) and value._value == self._value
