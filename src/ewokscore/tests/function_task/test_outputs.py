from collections import namedtuple
from dataclasses import dataclass
from typing import NamedTuple
from typing import TypedDict

import pytest
from ewoksutils.import_utils import qualname

from ...methodtask import get_method_task
from .shared_methods import PlainModel
from .shared_methods import RangeInfo
from .shared_methods import plain_model_method
from .shared_methods import range_info


def test_task_outputs_from_return_model(varinfo):
    task = get_method_task(qualname(range_info))(
        inputs={"a": 15, "b": 10}, varinfo=varinfo
    )
    task.execute()

    assert task.get_output_values() == {"extent": 5, "minimum": 10, "maximum": 15}


def test_task_outputs_from_plain_model(varinfo):
    task = get_method_task(qualname(plain_model_method))(
        inputs={"a": 2}, varinfo=varinfo
    )
    task.execute()

    assert task.get_output_values() == {"total": 3}


def no_return_type(a: int, b: int = 0):
    return a + b


def test_single_task_output(varinfo):
    task_class = get_method_task(qualname(no_return_type))
    assert set(task_class.output_names()) == {"return_value"}

    task = task_class(inputs={"a": 2, "b": 3}, varinfo=varinfo)
    task.execute()

    assert task.get_output_values() == {"return_value": 5}


class NamedTupleResult(NamedTuple):
    total: int
    count: int


def namedtuple_method(a: int, b: int) -> NamedTupleResult:
    return NamedTupleResult(total=a + b, count=2)


CollectionsResult = namedtuple("CollectionsResult", ["total", "count"])


def collections_namedtuple_method(a: int, b: int) -> CollectionsResult:
    return CollectionsResult(total=a + b, count=2)


@dataclass
class DataclassResult:
    total: int
    count: int


def dataclass_method(a: int, b: int) -> DataclassResult:
    return DataclassResult(total=a + b, count=2)


class TypedDictResult(TypedDict):
    total: int
    count: int


def typeddict_method(a: int, b: int) -> TypedDictResult:
    return TypedDictResult(total=a + b, count=2)


@pytest.mark.parametrize(
    "method",
    [
        namedtuple_method,
        collections_namedtuple_method,
        dataclass_method,
        typeddict_method,
    ],
    ids=lambda method: method.__name__,
)
def test_task_outputs_from_return_type(method, varinfo):
    task_class = get_method_task(qualname(method))
    assert set(task_class.output_names()) == {"total", "count"}

    task = task_class(inputs={"a": 2, "b": 3}, varinfo=varinfo)
    task.execute()

    assert task.get_output_values() == {"total": 5, "count": 2}


def mapping_method(a: float, b: float) -> RangeInfo:
    return {"extent": abs(b - a), "minimum": min(a, b), "maximum": max(a, b)}


def namedtuple_mapping_method(a: int, b: int) -> "NamedTupleResult":
    return {"total": a + b, "count": 2}


def collections_mapping_method(a: int, b: int) -> "CollectionsResult":
    return {"total": a + b, "count": 2}


def dataclass_mapping_method(a: int, b: int) -> "DataclassResult":
    return {"total": a + b, "count": 2}


def plain_model_mapping_method(a: int, b: int = 1) -> PlainModel:
    return {"total": a + b}


@pytest.mark.parametrize(
    "method,expected",
    [
        (mapping_method, {"extent": 5, "minimum": 10, "maximum": 15}),
        (plain_model_mapping_method, {"total": 25}),
        (namedtuple_mapping_method, {"total": 25, "count": 2}),
        (collections_mapping_method, {"total": 25, "count": 2}),
        (dataclass_mapping_method, {"total": 25, "count": 2}),
    ],
    ids=lambda value: getattr(value, "__name__", None),
)
def test_task_outputs_from_mapping(method, expected, varinfo):
    """A function may return a mapping instead of an instance of its return type."""
    task = get_method_task(qualname(method))(inputs={"a": 15, "b": 10}, varinfo=varinfo)
    task.execute()

    assert task.get_output_values() == expected
