"""Run ewoks Task as a Python function

The :func:`task_asfunction` function takes a ``task_identifier`` as input
and returns a function wrapping the corresponding Task.
"""

from __future__ import annotations

from collections import namedtuple
import functools
import importlib
from typing import Callable

from ewokscore.task_discovery import discover_all_tasks as _discover_all_tasks


def _find_task_info(task_identifier: str) -> tuple[dict[str, str]]:
    """Look for ewoks Task corresponding to task_identifier.

    The search is case insensitive.

    :param task_identifier: Task class name or fully qualified name to search
    :returns: Sequence of information for matching Task classes
    """
    # Store info in a mapping to prevent multiple entries for the same task
    tasks_info = {}
    for desc in _discover_all_tasks():
        if desc["task_type"] != "class":
            continue
        if desc["task_identifier"] == task_identifier or (
            desc["task_identifier"].rsplit(".", 1)[-1].lower()
            == task_identifier.lower()
        ):
            tasks_info[desc["task_identifier"]] = desc
    return tuple(tasks_info.values())


@functools.lru_cache(maxsize=None)
def task_asfunction(task_identifier: str) -> Callable:
    """Returns a function wrapping the given ewoks Task.

    Example:

    .. code:: python

       from ewokscore.wrap import task_asfunction

       sum_list_function = task_asfunction("SumList")

       result = sum_list_function(list=[1, 2, 3], delay=1)

    :param task_identifier: Task class name or fully qualified name to wrap
    :returns: Function wrapping the given ewoks Task
    :raises ValueError: If the task is not found of given task_identifier is ambiguous
    """
    selection = _find_task_info(task_identifier)
    if not selection:
        raise ValueError(f"No task found for id={task_identifier}")
    if len(selection) != 1:
        raise ValueError(
            f"Ambiguous id={task_identifier}, found: {[desc['task_identifier'] for desc in selection]}"
        )
    info = selection[0]

    module_name, class_name = info["task_identifier"].rsplit(".", 1)
    module = importlib.import_module(module_name)
    task_class = getattr(module, class_name)

    def wrapper(**kwargs):
        task = task_class(inputs=kwargs)
        task.execute()

        output_names = tuple(task.output_names())

        if not output_names:
            return None

        if len(output_names) == 1:  # Unpack single output
            return task.outputs[output_names[0]]

        output_namedtuple = namedtuple("TaskOutputs", output_names)
        return output_namedtuple(**{name: task.outputs[name] for name in output_names})

    wrapper.__name__ = class_name
    wrapper.__qualname__ = info["task_identifier"]
    wrapper.__module__ = module_name

    # Set docstring
    inputs_doc = "\n".join(f"\t{name}" for name in info["required_input_names"])
    inputs_doc += "\n"
    inputs_doc += "\n".join(
        f"\t{name} (optional)" for name in info["optional_input_names"]
    )

    output_names = info["output_names"]
    if not output_names:
        return_doc = "\tNone"
    if len(output_names) == 1:
        return_doc = f"\t{output_names[0]}"
    else:
        return_doc = "A namedtuple with the following fields:\n"
        return_doc += "/n".join(f"\t{name}" for name in output_names)

    wrapper.__doc__ = f"""Function to execute {info["task_identifier"]}

    {info["description"]}

    Parameters:
    {inputs_doc}

    Returns:
    {return_doc}
    """

    return wrapper
