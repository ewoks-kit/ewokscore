from typing import Union

import pytest

from ewokscore.missing_data import MISSING_DATA, MissingData, is_missing_data
from ewokscore.model import BaseInputModel
from ewokscore.task import Task, TaskInputError
from ewokscore.variable import Variable

from .examples.tasks.sumtask import SumTask


class User(BaseInputModel):
    id: int
    name: str = "Jane Doe"


class PassThroughTask(Task, input_model=User, output_names=["result"]):
    def run(self):
        self.outputs.result = self.get_input_values()


def test_error_if_input_model_does_not_derive_from_base_model():
    from pydantic import BaseModel

    class WrongBaseModelUser(BaseModel):
        id: int
        name: str = "Jane Doe"

    with pytest.raises(
        TypeError,
        match=r"input_model should be a subclass of ewokscore.model.BaseInputModel",
    ):

        class WrongPassThroughTask(Task, input_model=WrongBaseModelUser):
            pass


def test_error_if_input_model_used_with_input_names():
    with pytest.raises(TypeError, match="input_model cannot be used with input_names"):

        class WrongPassThroughTask(
            Task, input_model=User, input_names=["age"], output_names=["result"]
        ):
            pass


def test_validation():
    with pytest.raises(TaskInputError, match=r"id(\s*)Field required"):
        PassThroughTask(inputs={})

    with pytest.raises(TaskInputError, match=r"id(\s*)Input should be a valid integer"):
        PassThroughTask(inputs={"id": "wrong type"})


def test_default_value():
    task = PassThroughTask(inputs={"id": 5})
    assert task.get_input_values() == {"id": 5, "name": "Jane Doe"}


@pytest.mark.parametrize("value", [5, "wrong type"])
def test_wrapped_values(tmp_path, value):
    varinfo = {"root_uri": str(tmp_path / "task_results")}
    variable = Variable(value, varinfo=varinfo)
    variable.dump()
    varinfo = {"root_uri": str(tmp_path)}

    task = PassThroughTask(inputs={"id": variable})
    assert task.get_input_values() == {"id": value, "name": "Jane Doe"}

    task = PassThroughTask(inputs={"id": variable.uhash}, varinfo=varinfo)
    assert task.get_input_values() == {"id": value, "name": "Jane Doe"}

    task = PassThroughTask(inputs={"id": variable.data_uri})
    assert task.get_input_values() == {"id": value, "name": "Jane Doe"}

    task = PassThroughTask(inputs={"id": variable.data_proxy})
    assert task.get_input_values() == {"id": value, "name": "Jane Doe"}


def test_run():
    task = PassThroughTask(inputs={"id": 5, "name": "Smith"})
    task.execute()
    assert task.outputs["result"] == {"id": 5, "name": "Smith"}


def test_error_on_subclass_with_wrong_submodel():
    class Car(BaseInputModel):
        wheels: int

    with pytest.raises(
        TypeError,
        match="Input model (.*) from task subclass must be a subclass of the original task input model",
    ):

        class PassThroughCarTask(PassThroughTask, input_model=Car):
            pass


def test_error_on_subclass_with_input_names():
    with pytest.raises(
        TypeError,
        match="Cannot use input_names or optional_input_names",
    ):

        class ChildPassThroughTask(PassThroughTask, input_names=["age"]):
            pass


def test_error_on_subclass_with_input_model_if_input_names():
    with pytest.raises(
        TypeError,
        match="Cannot use input_model",
    ):

        class ChildPassThroughTask(SumTask, input_model=User):
            pass


def test_subclass_with_no_change():
    class ChildPassThroughTask(PassThroughTask):
        pass

    task = ChildPassThroughTask(inputs={"id": 5, "name": "Smith"})
    task.execute()
    assert task.outputs["result"] == {"id": 5, "name": "Smith"}


class SuperUser(User):
    age: int


class PassThroughSubTask(PassThroughTask, input_model=SuperUser):
    pass


def test_subclass_validation():
    with pytest.raises(TaskInputError, match=r"age(\s*)Field required"):
        PassThroughSubTask(inputs={"id": 5})


def test_subclass():
    task = PassThroughSubTask(inputs={"id": 5, "age": 18})
    task.execute()
    assert task.outputs["result"] == {"id": 5, "name": "Jane Doe", "age": 18}


def test_missing_data():
    class RegularTask(Task, input_names=["one"], optional_input_names=["two"]):
        pass

    class Model(BaseInputModel):
        one: int
        two: Union[int, MissingData] = MISSING_DATA

    class ModelTask(Task, input_model=Model):
        pass

    regular_task = RegularTask(inputs={"one": 1})
    model_task = ModelTask(inputs={"one": 1})
    assert (
        model_task.get_input_values() == regular_task.get_input_values() == {"one": 1}
    )
    assert (
        is_missing_data(model_task.get_input_value("two"))
        == is_missing_data(regular_task.get_input_value("two"))
        == True  # noqa: E712
    )
    assert (
        model_task.missing_inputs["two"]
        == regular_task.missing_inputs["two"]
        == True  # noqa: E712
    )
