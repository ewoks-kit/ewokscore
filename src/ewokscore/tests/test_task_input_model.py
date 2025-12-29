from dataclasses import dataclass
from typing import Union

import pytest
from pydantic import BaseModel
from pydantic import field_validator

from ..missing_data import MISSING_DATA
from ..missing_data import MissingData
from ..missing_data import is_missing_data
from ..model import BaseInputModel
from ..task import Task
from ..task import TaskInputError
from ..variable import Variable
from .examples.tasks.sumtask import SumTask


class User(BaseInputModel):
    id: int
    name: str = "Jane Doe"


class PassThroughTask(Task, input_model=User, output_names=["result"]):
    def run(self):
        self.outputs.result = self.get_input_values()


def test_error_if_input_model_does_not_derive_from_base_model():
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
    with pytest.raises(TaskInputError, match=r"Missing inputs.+\['id'\]"):
        PassThroughTask(inputs={})

    task = PassThroughTask(inputs={"id": "wrong type"})
    with pytest.raises(RuntimeError, match=r"id(\s*)Input should be a valid integer"):
        task.execute()


def test_default_value():
    task = PassThroughTask(inputs={"id": 5})
    task.execute()
    assert task.get_input_values() == {"id": 5, "name": "Jane Doe"}


def test_wrapped_value(tmp_path):
    varinfo = {"root_uri": str(tmp_path / "task_results")}
    variable = Variable(5, varinfo=varinfo)
    variable.dump()
    varinfo = {"root_uri": str(tmp_path)}

    task = PassThroughTask(inputs={"id": variable})
    task.execute()

    task = PassThroughTask(inputs={"id": variable.uhash}, varinfo=varinfo)
    task.execute()

    task = PassThroughTask(inputs={"id": variable.data_uri})
    task.execute()

    task = PassThroughTask(inputs={"id": variable.data_proxy})
    task.execute()


def test_wrapped_wrong_value(tmp_path):
    varinfo = {"root_uri": str(tmp_path / "task_results")}
    variable = Variable("wrong type", varinfo=varinfo)
    variable.dump()
    varinfo = {"root_uri": str(tmp_path)}

    task = PassThroughTask(inputs={"id": variable})
    with pytest.raises(RuntimeError, match=r"id(\s*)Input should be a valid integer"):
        task.execute()

    task = PassThroughTask(inputs={"id": variable.uhash}, varinfo=varinfo)
    with pytest.raises(RuntimeError, match=r"id(\s*)Input should be a valid integer"):
        task.execute()

    task = PassThroughTask(inputs={"id": variable.data_uri})
    with pytest.raises(RuntimeError, match=r"id(\s*)Input should be a valid integer"):
        task.execute()

    task = PassThroughTask(inputs={"id": variable.data_proxy})
    with pytest.raises(RuntimeError, match=r"id(\s*)Input should be a valid integer"):
        task.execute()


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
    with pytest.raises(TaskInputError, match=r"Missing inputs.+\['age'\]"):
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
    assert is_missing_data(model_task.get_input_value("two"))
    assert is_missing_data(regular_task.get_input_value("two"))
    assert model_task.missing_inputs["two"]
    assert regular_task.missing_inputs["two"]


class UserWithTypeCoercion(User):
    age: int

    @field_validator("age", mode="before")
    def coerce_age(cls, value):
        if isinstance(value, float):
            return int(value + 0.5)
        if not isinstance(value, int):
            return -1
        return value


class TaskWithTypeCoercion(Task, input_model=UserWithTypeCoercion):
    def run(self):
        pass


def test_input_type_coercion():
    task = TaskWithTypeCoercion(inputs={"id": 5, "age": 18})
    task.execute()
    assert task.get_input_values() == {"id": 5, "name": "Jane Doe", "age": 18}

    task = TaskWithTypeCoercion(inputs={"id": 5, "age": 18.1})
    task.execute()
    assert task.get_input_values() == {"id": 5, "name": "Jane Doe", "age": 18}

    task = TaskWithTypeCoercion(inputs={"id": 5, "age": "wrong type"})
    task.execute()
    assert task.get_input_values() == {"id": 5, "name": "Jane Doe", "age": -1}


def test_wrapped_type_coercion(tmp_path):
    varinfo = {"root_uri": str(tmp_path / "task_results")}
    variable = Variable(18.1, varinfo=varinfo)
    variable.dump()
    varinfo = {"root_uri": str(tmp_path)}

    coerced_input_values = {"id": 5, "name": "Jane Doe", "age": 18}

    inputs = {"id": 5, "name": "Jane Doe", "age": 18}
    task = TaskWithTypeCoercion(inputs=inputs, varinfo=varinfo)
    task.execute()
    assert task.get_input_values() == coerced_input_values
    coerced_variable_uhash = task.input_variables["age"].uhash
    # Includes input name "age" in hashing so not equal
    assert coerced_variable_uhash != variable.uhash

    inputs = {"id": 5, "name": "Jane Doe", "age": 18.1}
    task = TaskWithTypeCoercion(inputs=inputs, varinfo=varinfo)
    task.execute()
    assert task.get_input_values() == coerced_input_values
    uhash = task.input_variables["age"].uhash
    assert uhash == coerced_variable_uhash

    inputs = {"id": 5, "name": "Jane Doe", "age": Variable(18, varinfo=varinfo)}
    task = TaskWithTypeCoercion(inputs=inputs, varinfo=varinfo)
    task.execute()
    assert task.get_input_values() == coerced_input_values
    uhash = task.input_variables["age"].uhash
    assert uhash == Variable(18, varinfo=varinfo).uhash

    expected_uhash = uhash
    inputs = {"id": 5, "name": "Jane Doe", "age": Variable(18.1, varinfo=varinfo)}
    task = TaskWithTypeCoercion(inputs=inputs, varinfo=varinfo)
    task.execute()
    assert task.get_input_values() == coerced_input_values
    uhash = task.input_variables["age"].uhash
    assert uhash == expected_uhash

    uhash_before = variable.uhash
    inputs = {"id": 5, "name": "Jane Doe", "age": variable}
    task = TaskWithTypeCoercion(inputs=inputs, varinfo=varinfo)
    task.execute()
    assert task.get_input_values() == coerced_input_values
    input_variable = task.input_variables["age"]
    assert input_variable.uhash == variable.uhash
    assert variable.uhash != uhash_before

    # Reset variable since it got modified in-memory in the previous task execution
    varinfo = {"root_uri": str(tmp_path / "task_results")}
    variable = Variable(18.1, varinfo=varinfo)
    # No need for dump: was only modified in memory
    varinfo = {"root_uri": str(tmp_path)}
    fixed_uhash = variable.uhash

    for reference in [fixed_uhash, variable.data_uri, variable.data_proxy]:
        inputs = {"id": 5, "name": "Jane Doe", "age": reference}
        task = TaskWithTypeCoercion(inputs=inputs, varinfo=varinfo)
        task.execute()
        assert task.get_input_values() == coerced_input_values
        input_variable = task.input_variables["age"]
        assert input_variable.uhash == fixed_uhash
        assert variable.uhash == fixed_uhash


def test_dataclass_field_stays_dataclass():
    @dataclass
    class Address:
        city: str
        street: str

    class Inputs(BaseInputModel):
        address: Address

    class CheckAddress(Task, input_model=Inputs):
        def run(self):
            address = self.inputs.address
            assert isinstance(address, Address)

    task = CheckAddress(
        inputs={"address": Address(city="Grenoble", street="Jean-Jaurès")}
    )
    task.execute()
