from .task import Task
from .methodtask import MethodExecutorTask
from .scripttask import ScriptExecutorTask
from .ppftasks import PpfMethodExecutorTask
from .ppftasks import PpfPortTask
from .utils import import_method
from .utils import import_qualname

TASK_EXECUTABLE_ATTRIBUTE = (
    "class",
    "method",
    "ppfmethod",
    "ppfport",
    "script",
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


def raise_task_error(node_name, all=True):
    if node_name:
        node_name = " " + repr(node_name)
    if all:
        error_fmt = TASK_EXECUTABLE_ERROR_MSG_ALL
    else:
        error_fmt = TASK_EXECUTABLE_ERROR_MSG
    raise ValueError(error_fmt.format(node_name))


def task_executable_key(node_attrs, node_name="", all=False):
    if all:
        keys = TASK_EXECUTABLE_ATTRIBUTE_ALL
    else:
        keys = TASK_EXECUTABLE_ATTRIBUTE
    key = node_attrs.keys() & set(keys)
    if len(key) != 1:
        raise_task_error(node_name, all=all)
    key = key.pop()
    return key, node_attrs[key]


def validate_task_executable(node_attrs, node_name="", all=False):
    task_executable_key(node_attrs, node_name=node_name, all=all)


def get_varinfo(node_attrs, varinfo=None) -> dict:
    if varinfo is None:
        varinfo = dict()
    if node_attrs:
        varinfo.update(node_attrs.get("varinfo", dict()))
    return varinfo


def instantiate_task(node_attrs, varinfo=None, inputs=None, node_name=""):
    """
    :param dict node_attrs: node attributes of the graph representation
    :param dict varinfo: `Variable` constructor arguments
    :param dict or None inputs: dynamic inputs (from other tasks)
    :param str node_name:
    :returns Task:
    """
    # Static inputs
    task_inputs = dict(node_attrs.get("inputs", dict()))
    # Dynamic inputs (from other tasks)
    if inputs:
        task_inputs.update(inputs)
    # Variable persistence
    varinfo = get_varinfo(node_attrs, varinfo=varinfo)

    # Instantiate task
    key, value = task_executable_key(node_attrs, node_name=node_name)
    metadata = dict()
    if node_name:
        metadata["description"] = node_name
    if key == "class":
        return Task.instantiate(
            value, inputs=task_inputs, varinfo=varinfo, name=node_name
        )
    elif key == "method":
        task_inputs["method"] = value
        return MethodExecutorTask(inputs=task_inputs, varinfo=varinfo, name=node_name)
    elif key == "ppfmethod":
        task_inputs["method"] = value
        return PpfMethodExecutorTask(
            inputs=task_inputs, varinfo=varinfo, name=node_name
        )
    elif key == "ppfport":
        task_inputs["ppfport"] = value
        return PpfPortTask(inputs=task_inputs, varinfo=varinfo, name=node_name)
    elif key == "script":
        task_inputs["script"] = value
        return ScriptExecutorTask(inputs=task_inputs, varinfo=varinfo, name=node_name)
    else:
        raise_task_error(node_name, all=False)


def add_dynamic_inputs(dynamic_inputs, link_attrs, source_results):
    all_arguments = link_attrs.get("all_arguments", False)
    arguments = link_attrs.get("arguments", dict())
    if all_arguments and arguments:
        raise ValueError("'arguments' and 'all_arguments' cannot be used together")
    if all_arguments:
        arguments = {s: s for s in source_results}
        for from_arg in source_results:
            to_arg = from_arg
            dynamic_inputs[to_arg] = source_results[from_arg]

    for to_arg, from_arg in arguments.items():
        if from_arg:
            dynamic_inputs[to_arg] = source_results[from_arg]
        else:
            dynamic_inputs[to_arg] = source_results


def task_executable(node_attrs, node_name=""):
    key, value = task_executable_key(node_attrs, node_name=node_name)
    if key == "class":
        return value, import_qualname
    elif key == "method":
        return value, import_method
    elif key == "ppfmethod":
        return value, import_method
    elif key == "ppfport":
        return value, None
    elif key == "script":
        return value, None
    else:
        raise_task_error(node_name, all=False)


def get_task_class(node_attrs, node_name=""):
    key, value = task_executable_key(node_attrs, node_name=node_name)
    if key == "class":
        return Task.get_subclass(value)
    elif key == "method":
        return MethodExecutorTask
    elif key == "ppfmethod":
        return PpfMethodExecutorTask
    elif key == "ppfport":
        return PpfPortTask
    elif key == "script":
        return ScriptExecutorTask
    else:
        raise_task_error(node_name, all=False)
