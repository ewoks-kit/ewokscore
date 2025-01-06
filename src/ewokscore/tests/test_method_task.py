import sys
from collections import namedtuple
from dataclasses import dataclass
from typing import NamedTuple

import pytest

from ewoksutils.import_utils import qualname
from ewokscore.task import Task
from ewokscore.methodtask import get_method_task, task as task_decorator

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    TypedDict = None


def mymethod1(a=0, b=0):
    return a + b


def test_method_task1(varinfo):
    task_class = get_method_task(qualname(mymethod1))
    task = task_class(inputs={"a": 3, "b": 5}, varinfo=varinfo)
    task.execute()
    assert task.done
    assert task.get_output_values() == {"return_value": 8}


def mymethod2(*args):
    return sum(args)


def test_method_task2(varinfo):
    task_class = get_method_task(qualname(mymethod2))
    task = task_class(inputs={0: 3, 1: 5}, varinfo=varinfo)
    task.execute()
    assert task.done
    assert task.get_output_values() == {"return_value": 8}


def mymethod3(a, *args, b=None, c=3, **kw):
    print("a:", a)
    print("b:", b)
    print("c:", c)
    print("args:", args)
    print("kwargs:", kw)
    return a + sum(args) + b + c + sum(kw.values())


def test_method_task3(varinfo):
    task_class = get_method_task(qualname(mymethod3))
    task = task_class(inputs={0: 2, 1: 4, "b": 7, "d": 10}, varinfo=varinfo)
    task.execute()
    assert task.done
    assert task.get_output_values() == {"return_value": 26}


@dataclass
class DataClassReturn:
    x: int
    y: float


@task_decorator
def mymethod_dataclass() -> DataClassReturn:
    return DataClassReturn(x=1, y=2.5)


class TypedNamedTupleReturn(NamedTuple):
    x: int
    y: float


@task_decorator
def mymethod_typed_namedtuple() -> TypedNamedTupleReturn:
    return TypedNamedTupleReturn(x=1, y=2.5)


NamedTupleReturn = namedtuple("NamedTupleReturn", ["x", "y"])


@task_decorator
def mymethod_namedtuple() -> NamedTupleReturn:
    return NamedTupleReturn(x=1, y=2.5)


@pytest.mark.parametrize(
    "method", [mymethod_dataclass, mymethod_typed_namedtuple, mymethod_namedtuple]
)
def test_method_return(method, varinfo):
    task_class = get_method_task(qualname(method))
    task = task_class(inputs=None, varinfo=varinfo)
    task.execute()
    assert task.done
    assert task.get_output_values() == {"x": 1, "y": 2.5}


@pytest.mark.skipif(
    TypedDict is None,
    reason="TypedDict not available for this version of Python",
)
def test_method_return_typeddict(varinfo):
    global mymethod_typeddict

    class TypedDictReturn(TypedDict):
        x: int
        y: float

    @task_decorator
    def mymethod_typeddict() -> TypedDictReturn:
        return TypedDictReturn(x=1, y=2.5)

    task_class = get_method_task(qualname(mymethod_typeddict))
    task = task_class(inputs=None, varinfo=varinfo)
    task.execute()
    assert task.done
    assert task.get_output_values() == {
        "x": 1,
        "y": 2.5,
    }


def myppfmethod(a=0, b=0, **kw):
    return {"a": a + b}


def test_ppfmethod_task(varinfo):
    task = Task.instantiate(
        "PpfMethodExecutorTask",
        inputs={"_method": qualname(myppfmethod), "a": 3, "b": 5},
        varinfo=varinfo,
    )
    task.execute()
    assert task.done
    assert task.get_output_values() == {"_ppfdict": {"a": 8, "b": 5}}
