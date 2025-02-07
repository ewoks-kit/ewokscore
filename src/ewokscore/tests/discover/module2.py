from ewokscore import Task


class MyTask3(
    Task, input_names=["c"], optional_input_names=["d"], output_names=["result"]
):
    """Test 3"""

    def run(self):
        pass


def run(c, d=None):
    """Test"""
    pass


def myfunc(c, d=None):
    pass
