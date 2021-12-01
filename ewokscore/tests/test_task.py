import gc
import pytest
import json
from glob import glob
from pathlib import Path
from ewokscore.task import Task
from ewokscore.task import TaskInputError
from .examples.tasks.sumtask import SumTask


def find_files(tmpdir: Path, extension):
    return glob(str(tmpdir / "**" / "*" + extension), recursive=True)


def expected_task_output_storage(task):
    expected = [var.serialize() for var in task.output_variables.values()]
    expected.append(task.output_variables.serialize())
    return expected


def assert_storage(tmpdir, expected):
    lst = []
    for filename in find_files(tmpdir, ".json"):
        with open(filename, "r") as fileobj:
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
    expected = expected_task_output_storage(task)
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
    expected = expected_task_output_storage(task)
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
    expected += expected_task_output_storage(task)
    assert_storage(tmpdir, expected)

    task = SumTask({"a": task.output_variables["result"], "b": 0}, varinfo=varinfo)
    assert not task.done
    task.execute()
    assert task.done
    assert task.outputs.result == 12
    expected += expected_task_output_storage(task)
    assert_storage(tmpdir, expected)

    task = SumTask(
        {"a": 1, "b": task.output_variables["result"].data_proxy}, varinfo=varinfo
    )
    assert not task.done
    task.execute()
    assert task.done
    assert task.outputs.result == 13
    expected += expected_task_output_storage(task)
    assert_storage(tmpdir, expected)

    task = SumTask(
        {"a": 1, "b": task.output_variables["result"].data_proxy.uri}, varinfo=varinfo
    )
    assert not task.done
    task.execute()
    assert task.done
    assert task.outputs.result == 14
    expected += expected_task_output_storage(task)
    assert_storage(tmpdir, expected)


def test_task_required_positional_inputs():
    class MyTask(Task, n_required_positional_inputs=1):
        pass

    with pytest.raises(TaskInputError):
        MyTask()


def test_task_cleanup_references():
    class MyTask(Task, input_names=["mylist"], output_names=["mylist"]):
        def run(self):
            self.outputs.mylist = self.inputs.mylist + [len(self.inputs.mylist)]

    obj = [0, 1, 2]
    nref_start = len(gc.get_referrers(obj))
    task1 = MyTask(inputs={"mylist": obj})
    task2 = MyTask(inputs=task1.output_variables)
    task1.execute()
    task2.execute()
    assert len(gc.get_referrers(obj)) > nref_start

    uhash1 = task1.uhash
    uhashes1 = task1.output_uhashes
    uhash2 = task2.uhash
    uhashes2 = task2.output_uhashes

    task1.cleanup_references()

    while gc.collect():
        pass
    assert len(gc.get_referrers(obj)) == nref_start

    assert uhash1 == task1.uhash
    assert uhashes1 == task1.output_uhashes
    assert uhash2 == task2.uhash
    assert uhashes2 == task2.output_uhashes
