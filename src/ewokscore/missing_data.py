class MissingData:
    def __bool__(self):
        return False

    def __repr__(self):
        return "<MISSING_DATA>"

    def __eq__(self, other) -> bool:
        return isinstance(other, type(self))


MISSING_DATA = MissingData()


def is_missing_data(data):
    """This method solves the following issues when checking whether data is "missing":

    1. `myvar is MISSING_DATA`: problem when `MISSING_DATA` gets copied somehow
    2. `myvar == MISSING_DATA`: problem when `myvar` for example a `numpy` array
    """
    return isinstance(data, MissingData)
