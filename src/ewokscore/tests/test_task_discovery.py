from typing import List

import pytest

from .. import task_discovery
from .conftest import expected_tasks


@pytest.mark.parametrize("task_type", ["class", "method", "ppfmethod", None])
def test_discover_tasks_from_one_module(task_type):
    expected = expected_tasks("ewokscore.tests.discover.module1", task_type)

    tasks = task_discovery.discover_tasks_from_modules(
        "ewokscore.tests.discover.module1", task_type=task_type
    )
    assert_tasks(tasks, expected)
    assert len(tasks) == len(expected)


@pytest.mark.parametrize("task_type", ["class", "method", "ppfmethod", None])
def test_discover_tasks_from_module_pattern(task_type):
    expected = expected_tasks(task_type=task_type)

    tasks = task_discovery.discover_tasks_from_modules(
        "ewokscore.tests.discover.*", task_type=task_type
    )
    assert_tasks(tasks, expected)
    assert len(tasks) == len(expected)


def test_all_tasks_discovery():
    expected: List[task_discovery.TaskDict] = [
        {
            "category": "ewokscore",
            "optional_input_names": ["b", "delay"],
            "output_names": ["result", "too_small"],
            "required_input_names": ["a"],
            "task_identifier": "ewokscore.tests.examples.tasks.condsumtask.CondSumTask",
            "task_type": "class",
            "description": "Check whether a value is too small",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "category": "ewokscore",
            "optional_input_names": ["a", "b", "raise_error"],
            "output_names": ["result"],
            "required_input_names": [],
            "task_identifier": "ewokscore.tests.examples.tasks.errorsumtask.ErrorSumTask",
            "task_type": "class",
            "description": "Add two number with intentional exception",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "category": "ewokscore",
            "optional_input_names": [],
            "output_names": [],
            "required_input_names": [],
            "task_identifier": "ewokscore.tests.examples.tasks.nooutputtask.NoOutputTask",
            "task_type": "class",
            "description": "A task without outputs",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "category": "ewokscore",
            "optional_input_names": ["delay"],
            "output_names": ["sum"],
            "required_input_names": ["list"],
            "task_identifier": "ewokscore.tests.examples.tasks.sumlist.SumList",
            "task_type": "class",
            "description": "Add items from a list",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "category": "ewokscore",
            "optional_input_names": ["b", "delay"],
            "output_names": ["result"],
            "required_input_names": ["a"],
            "task_identifier": "ewokscore.tests.examples.tasks.sumtask.SumTask",
            "task_type": "class",
            "description": "Add two numbers with a delay",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "category": "ewokscore",
            "task_identifier": "ewokscore.tests.examples.tasks.addfunc.addfunc",
            "task_type": "method",
            "required_input_names": ["arg"],
            "optional_input_names": [],
            "output_names": ["return_value"],
            "description": "Add 1 to the first argument",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "category": "ewokscore",
            "task_identifier": "ewokscore.tests.examples.tasks.simplemethods.add",
            "task_type": "method",
            "required_input_names": [],
            "optional_input_names": [],
            "output_names": ["return_value"],
            "description": "Sum objects and add 1",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "category": "ewokscore",
            "task_identifier": "ewokscore.tests.examples.tasks.simplemethods.append",
            "task_type": "method",
            "required_input_names": [],
            "optional_input_names": [],
            "output_names": ["return_value"],
            "description": "Return positional arguments as a tuple",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
    ]

    tasks = task_discovery.discover_all_tasks()
    assert_tasks(tasks, expected)

    for task_type in ("class", "method", "ppfmethod"):
        tasks = task_discovery.discover_all_tasks(task_type=task_type)
        assert_tasks(
            tasks, [task for task in expected if task["task_type"] == task_type]
        )


def _find_task(tasks, identifier, task_type):
    for task in tasks:
        if task["task_identifier"] == identifier and task["task_type"] == task_type:
            return task

    raise ValueError(f"Task {identifier} and type {task_type} not found")


def assert_tasks(tasks, expected):
    for task in tasks:
        if task["category"] != "ewokscore":
            continue
        expected_task = _find_task(expected, task["task_identifier"], task["task_type"])
        for key, value in task.items():
            assert expected_task[key] == value
