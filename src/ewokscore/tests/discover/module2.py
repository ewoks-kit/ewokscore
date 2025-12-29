from ...model import BaseInputModel
from ...model import BaseOutputModel
from ...task import Task


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


class Task4Inputs(BaseInputModel):
    a: int
    b: float
    c: int = 0
    d: str = "DEFAULT"


class MyTask4(Task, input_model=Task4Inputs):
    pass


class Task5Outputs(BaseOutputModel):
    a: int
    b: float
    c: int = 0
    d: str = "DEFAULT"


class MyTask5(Task, output_model=Task5Outputs):
    pass
