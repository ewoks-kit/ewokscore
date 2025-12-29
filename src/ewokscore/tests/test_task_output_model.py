from dataclasses import dataclass

import pytest
from pydantic import BaseModel
from pydantic import field_validator

from ..model import BaseOutputModel
from ..task import Task
from .examples.tasks.sumtask import SumTask


class User(BaseOutputModel):
    id: int
    name: str = "Jane Doe"


class PassThroughTask(
    Task, input_names=["id"], optional_input_names=["name"], output_model=User
):
    def run(self):
        self.outputs.id = self.inputs.id
        if not self.missing_inputs.name:
            self.outputs.name = self.inputs.name


def test_error_if_output_model_does_not_derive_from_base_model():
    class WrongBaseModelUser(BaseModel):
        id: int
        name: str = "Jane Doe"

    with pytest.raises(
        TypeError,
        match=r"output_model should be a subclass of ewokscore.model.BaseOutputModel",
    ):

        class WrongPassThroughTask(Task, output_model=WrongBaseModelUser):
            pass


def test_error_if_output_model_used_with_output_names():
    with pytest.raises(
        TypeError, match="output_model cannot be used with output_names"
    ):

        class WrongPassThroughTask(Task, output_model=User, output_names=["user"]):
            pass


def test_validation():
    task = PassThroughTask(inputs={"id": "wrong type"})
    with pytest.raises(RuntimeError, match=r"id(\s*)Input should be a valid integer"):
        task.execute()


def test_default_value():
    task = PassThroughTask(inputs={"id": 5})
    task.execute()
    assert task.get_output_values() == {"id": 5, "name": "Jane Doe"}


def test_run():
    task = PassThroughTask(inputs={"id": 5, "name": "Smith"})
    task.execute()
    assert task.get_output_values() == {"id": 5, "name": "Smith"}


def test_error_on_subclass_with_wrong_submodel():
    class Car(BaseOutputModel):
        wheels: int

    with pytest.raises(
        TypeError,
        match="Output model (.*) from task subclass must be a subclass of the original task output model",
    ):

        class PassThroughCarTask(PassThroughTask, output_model=Car):
            pass


def test_error_on_subclass_with_output_names():
    with pytest.raises(
        TypeError,
        match="Cannot use output_names",
    ):

        class ChildPassThroughTask(PassThroughTask, output_names=["age"]):
            pass


def test_error_on_subclass_with_output_model_if_output_names():
    with pytest.raises(
        TypeError,
        match="Cannot use output_model",
    ):

        class ChildPassThroughTask(SumTask, output_model=User):
            pass


def test_subclass_with_no_change():
    class ChildPassThroughTask(PassThroughTask):
        pass

    task = ChildPassThroughTask(inputs={"id": 5, "name": "Smith"})
    task.execute()
    assert task.get_output_values() == {"id": 5, "name": "Smith"}


class SuperUser(User):
    age: int


class PassThroughSubTask(
    PassThroughTask, optional_input_names=["age"], output_model=SuperUser
):
    def run(self):
        super().run()
        if not self.missing_inputs.age:
            self.outputs.age = self.inputs.age


def test_subclass_validation():
    task = PassThroughSubTask(inputs={"id": 5})
    with pytest.raises(RuntimeError, match=r"1 validation error for SuperUser\nage"):
        task.execute()


def test_subclass():
    task = PassThroughSubTask(inputs={"id": 5, "age": 18})
    task.execute()
    assert task.get_output_values() == {"id": 5, "name": "Jane Doe", "age": 18}


class UserWithTypeCoercion(User):
    age: int

    @field_validator("age", mode="before")
    def coerce_age(cls, value):
        if isinstance(value, float):
            return int(value + 0.5)
        if not isinstance(value, int):
            return -1
        return value


class TaskWithTypeCoercion(PassThroughTask, output_model=UserWithTypeCoercion):

    def run(self):
        super().run()
        if not self.missing_inputs.age:
            self.outputs.age = self.inputs.age


def test_output_type_coercion():
    task = TaskWithTypeCoercion(inputs={"id": 5, "age": 18})
    task.execute()
    assert task.get_output_values() == {"id": 5, "name": "Jane Doe", "age": 18}

    task = TaskWithTypeCoercion(inputs={"id": 5, "age": 18.1})
    task.execute()
    assert task.get_output_values() == {"id": 5, "name": "Jane Doe", "age": 18}

    task = TaskWithTypeCoercion(inputs={"id": 5, "age": "wrong type"})
    task.execute()
    assert task.get_output_values() == {"id": 5, "name": "Jane Doe", "age": -1}


def test_wrapped_type_coercion(tmp_path):
    varinfo = {"root_uri": str(tmp_path / "task_results")}
    task = TaskWithTypeCoercion(inputs={"id": 5, "age": 18}, varinfo=varinfo)
    task.execute()
    coerced_output_values = {"id": 5, "name": "Jane Doe", "age": 18}
    assert task.get_output_values() == coerced_output_values


def test_dataclass_field_stays_dataclass():
    @dataclass
    class Address:
        city: str
        street: str

    class Outputs(BaseOutputModel):
        address: Address

    class CheckAddress(Task, input_names=["address"], output_model=Outputs):
        def run(self):
            self.outputs.address = self.inputs.address

    address = Address(city="Grenoble", street="Jean-Jaurès")
    task = CheckAddress(inputs={"address": address})
    task.execute()
    assert isinstance(task.get_output_value("address"), Address)
