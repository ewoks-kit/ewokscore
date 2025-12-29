from typing import List

import pytest
from ipykernel.kernelspec import install as install_kernel
from jupyter_client.kernelspec import KernelSpecManager
from packaging.version import parse as parse_version

from ..engine import CoreWorkflowEngine
from ..graph.schema import SchemaMetadata
from ..graph.schema import get_versions
from ..task_discovery import TaskDict


@pytest.fixture
def varinfo(tmp_path):
    yield {"root_uri": str(tmp_path)}


@pytest.fixture(scope="session")
def testkernel():
    m = KernelSpecManager()
    kernel_name = "pytest_kernel"
    install_kernel(kernel_name=kernel_name, user=True)
    yield kernel_name
    m.remove_kernel_spec(kernel_name)


@pytest.fixture
def use_test_schema_versions(monkeypatch):
    from ..graph import schema

    def no_update(graph):
        pass

    def backward_update(graph):
        graph.graph["schema_version"] = "0.1"

    def update_from_v0_2_to_1_0(graph):
        graph.graph["schema_version"] = "1.0"

    def get_test_versions():
        return {
            parse_version("0.1"): SchemaMetadata(("0.1.0-rc", None), no_update),
            parse_version("0.2"): SchemaMetadata(
                ("0.1.0-rc", None), update_from_v0_2_to_1_0
            ),
            parse_version("0.3"): SchemaMetadata(("0.1.0-rc", None), backward_update),
            **get_versions(),
        }

    monkeypatch.setattr(schema, "get_versions", get_test_versions)


def expected_tasks(module=None, task_type=None):
    CLASS_TASKS = [
        {
            "task_type": "class",
            "task_identifier": "ewokscore.tests.discover.module1.MyTask1",
            "required_input_names": ["a"],
            "optional_input_names": ["b"],
            "output_names": ["result"],
            "category": "ewokscore",
            "description": "Test 1",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "task_type": "class",
            "task_identifier": "ewokscore.tests.discover.module1.MyTask2",
            "required_input_names": ["a"],
            "optional_input_names": ["b"],
            "output_names": ["result"],
            "category": "ewokscore",
            "description": None,
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "task_type": "class",
            "task_identifier": "ewokscore.tests.discover.module1.MyTask3",
            "required_input_names": [],
            "optional_input_names": [],
            "output_names": [],
            "category": "ewokscore",
            "description": None,
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 2,
        },
        {
            "task_type": "class",
            "task_identifier": "ewokscore.tests.discover.module2.MyTask3",
            "required_input_names": ["c", "z"],
            "optional_input_names": ["d", "x"],
            "output_names": ["error", "result"],
            "category": "ewokscore",
            "description": "Test 3",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "task_type": "class",
            "task_identifier": "ewokscore.tests.discover.module2.MyTask4",
            "required_input_names": ["a", "b"],
            "optional_input_names": ["c", "d"],
            "output_names": [],
            "category": "ewokscore",
            "description": None,
            "input_model": "ewokscore.tests.discover.module2.Task4Inputs",
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "task_type": "class",
            "task_identifier": "ewokscore.tests.discover.module2.MyTask5",
            "required_input_names": [],
            "optional_input_names": [],
            "output_names": ["a", "b", "c", "d"],
            "category": "ewokscore",
            "description": None,
            "input_model": None,
            "output_model": "ewokscore.tests.discover.module2.Task5Outputs",
            "n_required_positional_inputs": 0,
        },
    ]

    METHOD_TASKS = [
        {
            "task_type": "method",
            "task_identifier": "ewokscore.tests.discover.module1.run",
            "required_input_names": ["a"],
            "optional_input_names": ["b"],
            "output_names": ["return_value"],
            "category": "ewokscore",
            "description": "Test 2",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "task_type": "method",
            "task_identifier": "ewokscore.tests.discover.module1.myfunc",
            "required_input_names": ["a"],
            "optional_input_names": ["b"],
            "output_names": ["return_value"],
            "category": "ewokscore",
            "description": None,
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "task_type": "method",
            "task_identifier": "ewokscore.tests.discover.module1.func_with_pos",
            "required_input_names": ["c"],
            "optional_input_names": [],
            "output_names": ["return_value"],
            "category": "ewokscore",
            "description": None,
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 2,
        },
        {
            "task_type": "method",
            "task_identifier": "ewokscore.tests.discover.module2.run",
            "required_input_names": ["z", "c"],
            "optional_input_names": ["x", "d"],
            "output_names": ["return_value"],
            "category": "ewokscore",
            "description": "Test",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "task_type": "method",
            "task_identifier": "ewokscore.tests.discover.module2.myfunc",
            "required_input_names": ["z", "c"],
            "optional_input_names": ["x", "d"],
            "output_names": ["return_value"],
            "category": "ewokscore",
            "description": None,
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
    ]

    PPFMETHOD_TASKS = [
        {
            "task_type": "ppfmethod",
            "task_identifier": "ewokscore.tests.discover.module1.run",
            "required_input_names": ["a"],
            "optional_input_names": ["b"],
            "output_names": ["return_value"],
            "category": "ewokscore",
            "description": "Test 2",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
        {
            "task_type": "ppfmethod",
            "task_identifier": "ewokscore.tests.discover.module2.run",
            "required_input_names": ["z", "c"],
            "optional_input_names": ["x", "d"],
            "output_names": ["return_value"],
            "category": "ewokscore",
            "description": "Test",
            "input_model": None,
            "output_model": None,
            "n_required_positional_inputs": 0,
        },
    ]

    TASKS: List[TaskDict] = [*CLASS_TASKS, *METHOD_TASKS, *PPFMETHOD_TASKS]

    if task_type is None and module is None:
        return TASKS

    if module is None:
        return [task for task in TASKS if task["task_type"] == task_type]

    if task_type is None:
        return [task for task in TASKS if module in task["task_identifier"]]

    return [
        task
        for task in TASKS
        if task["task_type"] == task_type and module in task["task_identifier"]
    ]


@pytest.fixture()
def engine():
    return CoreWorkflowEngine()
