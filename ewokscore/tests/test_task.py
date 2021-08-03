import pytest
import json
from ewokscore.task import Task
from ewokscore.task import TaskInputError
from .examples.tasks.sumtask import SumTask


def task_container_storage(task):
    return {k: v.data_proxy.uri.serialize() for k, v in task.output_variables.items()}


def assert_storage(tmpdir, expected):
    lst = []
    for fileobj in tmpdir.listdir():
        lst.append(json.load(fileobj))
    for v in lst:
        if isinstance(v, dict):
            v.pop("__traceback__", None)
    assert len(lst) == len(expected)
    for v in expected:
        lst.pop(lst.index(v))
    assert not lst, "Unexpected data saved"


def test_no_public_reserved_names():
    assert not [s for s in Task._reserved_variable_names() if not s.startswith("_")]


def test_task_missing_input():
    with pytest.raises(TaskInputError):
        SumTask()


def test_task_readonly_input():
    task = SumTask(inputs={"a": 10})
    with pytest.raises(RuntimeError):
        task.inputs.a = 10


def test_task_optional_input(tmpdir, varinfo):
    task = SumTask(inputs={"a": 10}, varinfo=varinfo)
    assert not task.done
    task.execute()
    assert task.done
    assert task.outputs.result == 10
    expected = [task_container_storage(task), 10]
    assert_storage(tmpdir, expected)


def test_task_done(varinfo):
    task = SumTask(inputs={"a": 10}, varinfo=varinfo)
    assert not task.done
    task.execute()
    assert task.done

    task = SumTask(inputs={"a": 10}, varinfo=varinfo)
    assert task.done

    task = SumTask(inputs={"a": 10})
    assert not task.done
    task.execute()
    assert task.done

    task = SumTask(inputs={"a": 10})
    assert not task.done


def test_task_uhash(varinfo):
    task = SumTask(inputs={"a": 10}, varinfo=varinfo)
    uhash = task.uhash
    assert task.uhash == task.output_variables.uhash
    assert task.uhash != task.input_variables.uhash

    task.input_variables["a"].value += 1
    assert task.uhash != uhash
    assert task.uhash == task.output_variables.uhash
    assert task.uhash != task.input_variables.uhash


def test_task_storage(tmpdir, varinfo):
    task = SumTask(inputs={"a": 10, "b": 2}, varinfo=varinfo)
    assert not task.done
    task.execute()
    assert task.done
    assert task.outputs.result == 12
    expected = [task_container_storage(task), 12]
    assert_storage(tmpdir, expected)

    task = SumTask(inputs={"a": 10, "b": 2}, varinfo=varinfo)
    assert task.done
    assert task.outputs.result == 12
    assert_storage(tmpdir, expected)

    task = SumTask({"a": 2, "b": 10}, varinfo=varinfo)
    assert not task.done
    task.execute()
    assert task.done
    assert task.outputs.result == 12
    expected += [task_container_storage(task), 12]
    assert_storage(tmpdir, expected)

    task = SumTask({"a": task.output_variables["result"], "b": 0}, varinfo=varinfo)
    assert not task.done
    task.execute()
    assert task.done
    assert task.outputs.result == 12
    expected += [task_container_storage(task), 12]
    assert_storage(tmpdir, expected)

    task = SumTask(
        {"a": 1, "b": task.output_variables["result"].uhash}, varinfo=varinfo
    )
    assert not task.done
    task.execute()
    assert task.done
    assert task.outputs.result == 13
    expected += [task_container_storage(task), 13]
    assert_storage(tmpdir, expected)


def test_task_required_positional_inputs():
    class MyTask(Task, n_required_positional_inputs=1):
        pass

    with pytest.raises(TaskInputError):
        MyTask()
