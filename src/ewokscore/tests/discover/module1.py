from ...task import Task


class MyTask1(
    Task, input_names=["a"], optional_input_names=["b"], output_names=["result"]
):
    """Test 1"""

    def run(self):
        pass


class MyTask2(
    Task, input_names=["a"], optional_input_names=["b"], output_names=["result"]
):
    def run(self):
        pass


class MyTask3(Task, n_required_positional_inputs=2):
    def run(self):
        pass


def run(a, b=None):
    """Test 2"""
    pass


def myfunc(a, b=None):
    pass


def func_with_pos(a, b, /, c):
    pass


def _myfunc(a, b=None):
    pass


class _MyTask2(Task):
    def run(self):
        pass


class UnregisteredTask(Task, register=False):
    def run(self):
        pass
