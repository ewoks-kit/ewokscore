from functools import partial
from typing import Optional, Tuple
import warnings
from .task import Task
from .methodtask import MethodExecutorTask
from .scripttask import ScriptExecutorTask
from .ppftasks import PpfMethodExecutorTask
from .ppftasks import PpfPortTask
from .dynamictask import get_dynamically_task_class
from .utils import import_method
from .utils import import_qualname
from .node import get_node_label
from .node import NodeIdType


TASK_EXECUTABLE_ATTRIBUTE = (
    "class",
    "method",
    "ppfmethod",
    "ppfport",
    "script",
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
    node_attrs: dict, node_id: NodeIdType = "", all: bool = False
) -> Tuple[str, dict]:
    if all:
        keys = TASK_EXECUTABLE_ATTRIBUTE_ALL
    else:
        keys = TASK_EXECUTABLE_ATTRIBUTE
    key = node_attrs.keys() & set(keys)
    if len(key) != 1:
        node_label = get_node_label(node_attrs, node_id=node_id)
        raise_task_error(node_label, all=all)
    key = key.pop()

    if key == "task_type":
        task_type = node_attrs[key]
    else:
        warnings.warn(
            f"'{key}' is deprecated in favor of 'task_type' with 'task_identifier'",
            FutureWarning,
        )
        value = node_attrs.pop(key)
        if key != "ppfport":
            node_attrs["task_identifier"] = value
        if key == "task":
            task_type = "generated"
        else:
            task_type = key
        node_attrs["task_type"] = task_type
    if task_type == "generated":
        if "task_generator" not in node_attrs:
            raise ValueError("node attribute 'task_generator' is missing")
    else:
        if "task_generator" in node_attrs:
            raise ValueError(
                "node attribute 'task_generator' should only be specified when 'task_type' is 'generated'"
            )
    if task_type == "ppfport":
        if "task_identifier" in node_attrs:
            raise ValueError(
                "node attribute 'task_identifier' should not be used when 'task_type' is 'ppfport'"
            )
    else:
        if "task_identifier" not in node_attrs:
            raise ValueError("node attribute 'task_identifier' is missing")

    info = dict()
    if task_type != "ppfport":
        info["task_identifier"] = node_attrs["task_identifier"]
    if task_type == "generated":
        info["task_generator"] = node_attrs["task_generator"]
    return task_type, info


def validate_task_executable(
    node_attrs: dict, node_id: NodeIdType = "", all: bool = False
):
    task_executable_info(node_attrs, node_id=node_id, all=all)


def get_varinfo(node_attrs: dict, varinfo: Optional[dict] = None) -> dict:
    if varinfo is None:
        varinfo = dict()
    if node_attrs:
        varinfo.update(node_attrs.get("varinfo", dict()))
    return varinfo


def instantiate_task(
    node_attrs: dict,
    varinfo: Optional[dict] = None,
    inputs: Optional[dict] = None,
    node_id: NodeIdType = "",
):
    """
    :param dict node_attrs: node attributes of the graph representation
    :param dict varinfo: `Variable` constructor arguments
    :param dict or None inputs: dynamic inputs (from other tasks)
    :param str node_id:
    :returns Task:
    """
    # Default inputs
    task_inputs = node_attrs.get("default_inputs", list())
    task_inputs = {d["name"]: d["value"] for d in task_inputs}
    # Dynamic inputs (from other tasks)
    if inputs:
        task_inputs.update(inputs)
    # Variable persistence
    varinfo = get_varinfo(node_attrs, varinfo=varinfo)

    # Instantiate task
    task_type, task_info = task_executable_info(node_attrs, node_id=node_id)
    node_label = get_node_label(node_attrs, node_id=node_id)
    if task_type == "class":
        return Task.instantiate(
            task_info["task_identifier"],
            inputs=task_inputs,
            varinfo=varinfo,
            label=node_label,
        )
    elif task_type == "method":
        task_inputs[MethodExecutorTask.METHOD_ARGUMENT] = task_info["task_identifier"]
        return MethodExecutorTask(inputs=task_inputs, varinfo=varinfo, label=node_label)
    elif task_type == "ppfmethod":
        task_inputs[PpfMethodExecutorTask.METHOD_ARGUMENT] = task_info[
            "task_identifier"
        ]
        return PpfMethodExecutorTask(
            inputs=task_inputs, varinfo=varinfo, label=node_label
        )
    elif task_type == "ppfport":
        return PpfPortTask(inputs=task_inputs, varinfo=varinfo, label=node_label)
    elif task_type == "script":
        task_inputs[ScriptExecutorTask.SCRIPT_ARGUMENT] = task_info["task_identifier"]
        return ScriptExecutorTask(inputs=task_inputs, varinfo=varinfo, label=node_label)
    elif task_type == "generated":
        task_class = get_dynamically_task_class(
            node_attrs.get("task_generator"), task_info["task_identifier"]
        )
        return task_class(inputs=task_inputs, varinfo=varinfo, label=node_label)
    else:
        raise_task_error(node_label, all=False)


def add_dynamic_inputs(dynamic_inputs: dict, link_attrs: dict, source_results: dict):
    map_all_data = link_attrs.get("map_all_data", False)
    data_mapping = link_attrs.get("data_mapping", list())
    if map_all_data and data_mapping:
        raise ValueError("'data_mapping' and 'map_all_data' cannot be used together")
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
            raise KeyError(f"Argument '{arg}' is missing an 'input' key") from None
        if output_arg:
            try:
                dynamic_inputs[input_arg] = source_results[output_arg]
            except KeyError:
                raise KeyError(
                    f"'{output_arg}' is not an output variable of the source task"
                ) from None
        else:
            dynamic_inputs[input_arg] = source_results


def task_executable(node_attrs: dict, node_id: NodeIdType = ""):
    task_type, task_info = task_executable_info(node_attrs, node_id=node_id)
    if task_type == "class":
        return task_info["task_identifier"], import_qualname
    elif task_type == "method":
        return task_info["task_identifier"], import_method
    elif task_type == "ppfmethod":
        return task_info["task_identifier"], import_method
    elif task_type == "ppfport":
        return None, None
    elif task_type == "script":
        return task_info["task_identifier"], None
    elif task_type == "generated":
        return task_info["task_identifier"], partial(
            get_dynamically_task_class, node_attrs.get("task_generator")
        )
    else:
        node_label = get_node_label(node_attrs, node_id=node_id)
        raise_task_error(node_label, all=False)


def get_task_class(node_attrs: dict, node_id: NodeIdType = ""):
    task_type, task_info = task_executable_info(node_attrs, node_id=node_id)
    if task_type == "class":
        return Task.get_subclass(task_info["task_identifier"])
    elif task_type == "method":
        return MethodExecutorTask
    elif task_type == "ppfmethod":
        return PpfMethodExecutorTask
    elif task_type == "ppfport":
        return PpfPortTask
    elif task_type == "script":
        return ScriptExecutorTask
    elif task_type == "task":
        return get_dynamically_task_class(
            node_attrs.get("task_generator"), task_info["task_identifier"]
        )
    else:
        node_label = get_node_label(node_attrs, node_id=node_id)
        raise_task_error(node_label, all=False)
