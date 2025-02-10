from ewokscore import Task


class MyTask3(
    Task,
    input_names=["z", "c"],
    optional_input_names=["x", "d"],
    output_names=["result", "error"],
):
    """Test 3"""

    def run(self):
        pass


def run(z, c, x=None, d=None):
    """Test"""
    pass


def myfunc(z, c, x=None, d=None):
    pass
