import os
import sys

import pytest

from ..inittask import instantiate_task
from ..task import Task
from .examples import tasks


@pytest.fixture(scope="module")
def notebook():
    return os.path.join(tasks.__path__[0], "notebooktask.ipynb")


@pytest.mark.xfail(sys.version_info < (3, 8), reason="papermill #711", strict=False)
def test_notebook_task(notebook, testkernel):
    task = Task.instantiate(
        "NotebookExecutorTask",
        inputs={
            "_notebook": notebook,
            "_kernel_name": testkernel,
            "_execution_timeout": 60,
            "a": 3,
            "b": 5,
        },
    )
    task.execute()
    assert task.done
    assert task.succeeded
    expected = {
        "output_notebook": None,
        "results": {"result": 8, "x": "string", "y": 10, "z": [1, 2, 3]},
    }
    assert task.get_output_values() == expected


@pytest.mark.xfail(sys.version_info < (3, 8), reason="papermill #711", strict=False)
def test_notebook_task_save(tmp_path, notebook, testkernel):
    output_notebook = tmp_path / "nb.ipynb"
    notebook = os.path.join(tasks.__path__[0], "notebooktask.ipynb")
    task = Task.instantiate(
        "NotebookExecutorTask",
        inputs={
            "_notebook": notebook,
            "_output_notebook": str(output_notebook),
            "_kernel_name": testkernel,
            "_execution_timeout": 60,
            "a": 3,
            "b": 5,
        },
    )
    task.execute()
    assert task.done
    assert task.succeeded
    expected = {
        "output_notebook": str(output_notebook),
        "results": {"result": 8, "x": "string", "y": 10, "z": [1, 2, 3]},
    }
    assert task.get_output_values() == expected
    assert output_notebook.exists()


@pytest.mark.xfail(sys.version_info < (3, 8), reason="papermill #711", strict=False)
def test_notebook_task_failure(notebook, testkernel):
    task = Task.instantiate(
        "NotebookExecutorTask",
        inputs={
            "_notebook": notebook,
            "_kernel_name": testkernel,
            "_execution_timeout": 60,
            "a": "wrong value",
            "b": 10,
        },
    )
    with pytest.raises(RuntimeError):
        task.execute()
    assert task.done
    assert task.failed


@pytest.mark.xfail(sys.version_info < (3, 8), reason="papermill #711", strict=False)
def test_task_class_generator(notebook, testkernel):
    task = instantiate_task(
        "node_id",
        {
            "task_type": "notebook",
            "task_identifier": notebook,
        },
        inputs={
            "_kernel_name": testkernel,
            "_execution_timeout": 60,
            "a": 3,
            "b": 5,
        },
    )
    task.execute()

    assert task.done
    assert task.succeeded
    expected = {
        "output_notebook": None,
        "results": {"result": 8, "x": "string", "y": 10, "z": [1, 2, 3]},
    }
    assert task.get_output_values() == expected
