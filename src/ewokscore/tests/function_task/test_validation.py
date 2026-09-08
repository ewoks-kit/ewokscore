import sys

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

import numpy
import pytest
from ewoksutils.import_utils import qualname
from pydantic import ConfigDict
from pydantic import Field
from pydantic import ValidationError
from pydantic import validate_call

from ...methodtask import get_method_task
from ...model import BaseOutputModel
from .shared_methods import RangeInfo
from .shared_methods import range_info


def invalid_output_method(a: float, b: float) -> RangeInfo:
    return {"extent": "not a number", "minimum": a, "maximum": b}


def test_task_input_validation(varinfo):
    task = get_method_task(qualname(range_info))(
        inputs={"a": "not a number", "b": 10}, varinfo=varinfo
    )
    with pytest.raises(Exception, match="Invalid task inputs"):
        task.execute(raise_on_error=True)


def test_task_output_validation(varinfo):
    task = get_method_task(qualname(invalid_output_method))(
        inputs={"a": 15, "b": 10}, varinfo=varinfo
    )
    with pytest.raises(Exception, match="Invalid task outputs"):
        task.execute(raise_on_error=True)


class DescribedResult(BaseOutputModel):
    total: int = Field(..., description="Sum of the two numbers")


def annotated_method(
    a: Annotated[int, Field(description="First number")],
    b: Annotated[int, Field(description="Second number", ge=0)] = 0,
) -> DescribedResult:
    return DescribedResult(total=a + b)


def field_default_method(
    a: int = Field(..., description="First number"),
    b: int = Field(0, description="Second number", ge=0),
) -> DescribedResult:
    return DescribedResult(total=a + b)


@pytest.mark.parametrize(
    "method", [annotated_method, field_default_method], ids=lambda m: m.__name__
)
def test_described_task_inputs_and_outputs(method, varinfo):
    task_class = get_method_task(qualname(method))

    assert set(task_class.required_input_names()) == {"a"}
    assert set(task_class.optional_input_names()) == {"b"}

    input_fields = task_class.input_model().model_fields
    assert input_fields["a"].description == "First number"
    assert input_fields["b"].description == "Second number"
    assert task_class.output_model().model_fields["total"].description == (
        "Sum of the two numbers"
    )

    task = task_class(inputs={"a": 2, "b": 3}, varinfo=varinfo)
    task.execute()
    assert task.get_output_values() == {"total": 5}


@pytest.mark.parametrize(
    "method", [annotated_method, field_default_method], ids=lambda m: m.__name__
)
def test_task_input_constraint(method, varinfo):
    task = get_method_task(qualname(method))(inputs={"a": 2, "b": -1}, varinfo=varinfo)
    with pytest.raises(Exception, match="Invalid task inputs"):
        task.execute(raise_on_error=True)


@validate_call(validate_return=True)
def validated_method(a: float, b: float = 0) -> RangeInfo:
    return RangeInfo(extent=abs(b - a), minimum=min(a, b), maximum=max(a, b))


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def validated_arbitrary_method(data: numpy.ndarray) -> int:
    return data.size


def test_validate_call_task_signature():
    task_class = get_method_task(qualname(validated_method))

    assert set(task_class.required_input_names()) == {"a"}
    assert set(task_class.optional_input_names()) == {"b"}
    assert set(task_class.output_names()) == {"extent", "minimum", "maximum"}


def test_validate_call_task_execution(varinfo):
    task = get_method_task(qualname(validated_method))(
        inputs={"a": 15, "b": 10}, varinfo=varinfo
    )
    task.execute()

    assert task.get_output_values() == {"extent": 5, "minimum": 10, "maximum": 15}


def test_validate_call_arbitrary_type(varinfo):
    task = get_method_task(qualname(validated_arbitrary_method))(
        inputs={"data": numpy.arange(4)}, varinfo=varinfo
    )
    task.execute()

    assert task.get_output_values() == {"return_value": 4}


def test_validate_call_direct_call():
    assert validated_method(15, 10) == RangeInfo(extent=5, minimum=10, maximum=15)

    with pytest.raises(ValidationError):
        validated_method("not a number")


@validate_call(validate_return=True)
def invalid_return_method(a: float) -> RangeInfo:
    return {"extent": "not a number", "minimum": a, "maximum": a}


def test_validate_call_direct_call_return():
    with pytest.raises(ValidationError):
        invalid_return_method(1)
