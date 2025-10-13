import warnings
from functools import partial
from typing import Optional
from typing import Tuple

from ewoksutils.import_utils import import_method
from ewoksutils.import_utils import import_qualname

from .dynamictask import get_dynamically_task_class
from .methodtask import MethodExecutorTask
from .node import NodeIdType
from .node import get_node_label
from .notebooktask import NotebookExecutorTask
from .ppftasks import PpfMethodExecutorTask
from .ppftasks import PpfPortTask
from .scripttask import ScriptExecutorTask
from .task import Task

TASK_EXECUTABLE_ATTRIBUTE = (
    "class",
    "method",
    "ppfmethod",
    "ppfport",
    "script",
    "notebook",
    "task",
    "task_type",
)

TASK_EXECUTABLE_ATTRIBUTE_ALL = TASK_EXECUTABLE_ATTRIBUTE + ("graph",)

TASK_EXECUTABLE_ATTRIBUTE_STR = (
    ", ".join(map(repr, TASK_EXECUTABLE_ATTRIBUTE[:-1]))
    + " or "
    + repr(TASK_EXECUTABLE_ATTRIBUTE[-1])
)

TASK_EXECUTABLE_ATTRIBUTE_ALL_STR = (
    ", ".join(map(repr, TASK_EXECUTABLE_ATTRIBUTE_ALL[:-1]))
    + " or "
    + repr(TASK_EXECUTABLE_ATTRIBUTE_ALL[-1])
)
TASK_EXECUTABLE_ERROR_MSG = f"Task{{}} requires the {TASK_EXECUTABLE_ATTRIBUTE_STR} key"
TASK_EXECUTABLE_ERROR_MSG_ALL = (
    f"Task{{}} requires the {TASK_EXECUTABLE_ATTRIBUTE_ALL_STR} key"
)


def raise_task_error(node_label: str, all: bool = True):
    if node_label:
        node_label = " " + repr(node_label)
    if all:
        error_fmt = TASK_EXECUTABLE_ERROR_MSG_ALL
    else:
        error_fmt = TASK_EXECUTABLE_ERROR_MSG
    raise ValueError(error_fmt.format(node_label))


def task_executable_info(
    node_id: NodeIdType, node_attrs: dict, all: bool = False
) -> Tuple[str, dict]:
    if all:
        keys = TASK_EXECUTABLE_ATTRIBUTE_ALL
    else:
        keys = TASK_EXECUTABLE_ATTRIBUTE
    key = node_attrs.keys() & set(keys)
    if len(key) != 1:
        node_label = get_node_label(node_id, node_attrs)
        raise_task_error(node_label, all=all)
    key = key.pop()

    if key == "task_type":
        task_type = node_attrs[key]
    else:
        warnings.warn(
            f"'{key}' is deprecated in favor of 'task_type' with 'task_identifier'",
            DeprecationWarning,
        )
        value = node_attrs.pop(key)
        if key != "ppfport":
            node_attrs["task_identifier"] = value
        if key == "task":
            task_type = "generated"
        else:
            task_type = key
        node_attrs["task_type"] = task_type

    has_task_generator = bool(node_attrs.get("task_generator"))
    if task_type == "generated":
        if not has_task_generator:
            raise ValueError("node attribute 'task_generator' is missing")
    elif has_task_generator:
        raise ValueError(
            "node attribute 'task_generator' should only be specified when 'task_type' is 'generated'"
        )

    has_task_identifier = bool(node_attrs.get("task_identifier"))
    if task_type == "ppfport":
        if has_task_identifier:
            raise ValueError(
                "node attribute 'task_identifier' should not be used when 'task_type' is 'ppfport'"
            )
    elif not has_task_identifier:
        raise ValueError("node attribute 'task_identifier' is missing")

    info = dict()
    if task_type != "ppfport":
        info["task_identifier"] = node_attrs["task_identifier"]
    if task_type == "generated":
        info["task_generator"] = node_attrs["task_generator"]
    return task_type, info


def validate_task_executable(node_id: NodeIdType, node_attrs: dict, all: bool = False):
    task_executable_info(node_id, node_attrs, all=all)


def instantiate_task(
    node_id: NodeIdType,
    node_attrs: dict,
    inputs: Optional[dict] = None,
    varinfo: Optional[dict] = None,
    execinfo: Optional[dict] = None,
    task_options: Optional[dict] = None,
) -> Task:
    """
    :param node_id:
    :param node_attrs: node attributes of the graph representation
    :param inputs: dynamic inputs (from other tasks)
    :param varinfo: `Variable` constructor arguments
    :param execinfo:
    :returns Task:
    """
    # Default inputs
    task_inputs = node_attrs.get("default_inputs", list())
    task_inputs = {d["name"]: d["value"] for d in task_inputs}
    # Dynamic inputs (from other tasks)
    if inputs:
        task_inputs.update(inputs)

    # Instantiate task
    task_type, task_info = task_executable_info(node_id, node_attrs)
    if task_options:
        task_kwargs = dict(task_options)
    else:
        task_kwargs = dict()
    task_kwargs.update(
        inputs=task_inputs,
        varinfo=varinfo,
        node_id=node_id,
        node_attrs=node_attrs,
        execinfo=execinfo,
    )
    if task_type == "class":
        return Task.instantiate(task_info["task_identifier"], **task_kwargs)

    if task_type == "method":
        task_inputs[MethodExecutorTask.METHOD_ARGUMENT] = task_info["task_identifier"]
        return MethodExecutorTask(**task_kwargs)

    if task_type == "ppfmethod":
        task_inputs[PpfMethodExecutorTask.METHOD_ARGUMENT] = task_info[
            "task_identifier"
        ]
        return PpfMethodExecutorTask(**task_kwargs)

    if task_type == "ppfport":
        return PpfPortTask(**task_kwargs)

    if task_type == "script":
        task_inputs[ScriptExecutorTask.SCRIPT_ARGUMENT] = task_info["task_identifier"]
        return ScriptExecutorTask(**task_kwargs)

    if task_type == "notebook":
        task_inputs[NotebookExecutorTask.NOTEBOOK_ARGUMENT] = task_info[
            "task_identifier"
        ]
        return NotebookExecutorTask(**task_kwargs)

    if task_type == "generated":
        task_class = get_dynamically_task_class(
            node_attrs.get("task_generator"), task_info["task_identifier"]
        )
        return task_class(**task_kwargs)

    node_label = get_node_label(node_id, node_attrs)
    raise_task_error(node_label, all=False)


def add_dynamic_inputs(
    dynamic_inputs: dict,
    link_attrs: dict,
    source_results: dict,
    source_id: Optional[NodeIdType] = None,
    target_id: Optional[NodeIdType] = None,
):
    err_suffix = ""
    if source_id or target_id:
        err_suffix = f" (Link '{source_id}' -> '{target_id}')"
    map_all_data = link_attrs.get("map_all_data", False)
    data_mapping = link_attrs.get("data_mapping", list())
    if map_all_data and data_mapping:
        raise ValueError(
            f"'data_mapping' and 'map_all_data' cannot be used together{err_suffix}"
        )
    if map_all_data:
        data_mapping = [{"target_input": s, "source_output": s} for s in source_results]
        for from_arg in source_results:
            to_arg = from_arg
            dynamic_inputs[to_arg] = source_results[from_arg]
    for arg in data_mapping:
        output_arg = arg.get("source_output")
        try:
            input_arg = arg["target_input"]
        except KeyError:
            raise KeyError(
                f"Argument '{arg}' is missing an 'input' key{err_suffix}"
            ) from None
        if output_arg:
            try:
                dynamic_inputs[input_arg] = source_results[output_arg]
            except KeyError:
                raise KeyError(
                    f"'{output_arg}' is not an output variable of the source node{err_suffix}"
                ) from None
        else:
            dynamic_inputs[input_arg] = source_results


def task_executable(node_id: NodeIdType, node_attrs: dict):
    task_type, task_info = task_executable_info(node_id, node_attrs)
    if task_type == "class":
        return task_info["task_identifier"], import_qualname
    if task_type == "method":
        return task_info["task_identifier"], import_method
    if task_type == "ppfmethod":
        return task_info["task_identifier"], import_method
    if task_type == "ppfport":
        return None, None
    if task_type == "script":
        return task_info["task_identifier"], None
    if task_type == "notebook":
        return task_info["task_identifier"], None
    if task_type == "generated":
        return task_info["task_identifier"], partial(
            get_dynamically_task_class, node_attrs.get("task_generator")
        )
    node_label = get_node_label(node_id, node_attrs)
    raise_task_error(node_label, all=False)


def get_task_class(node_id: NodeIdType, node_attrs: dict):
    task_type, task_info = task_executable_info(node_id, node_attrs)
    if task_type == "class":
        return Task.get_subclass(task_info["task_identifier"])
    if task_type == "method":
        return MethodExecutorTask
    if task_type == "ppfmethod":
        return PpfMethodExecutorTask
    if task_type == "ppfport":
        return PpfPortTask
    if task_type == "script":
        return ScriptExecutorTask
    if task_type == "notebook":
        return NotebookExecutorTask
    if task_type == "task":
        return get_dynamically_task_class(
            node_attrs.get("task_generator"), task_info["task_identifier"]
        )

    node_label = get_node_label(node_id, node_attrs)
    raise_task_error(node_label, all=False)
