import inspect
import importlib
import importlib.util
from typing import Callable, Iterable, Optional
from .task import Task
from ewoksutils.import_utils import qualname


def discover_tasks_from_modules(
    *module_names: Iterable[str], task_type="class"
) -> Iterable[dict]:
    if task_type == "method":
        yield from _iter_method_tasks(*module_names)
    elif task_type == "ppfmethod":
        yield from _iter_method_tasks(
            *module_names, filter_method_name=lambda name: name == "run"
        )
    elif task_type == "class":
        for module_name in module_names:
            importlib.import_module(module_name)
        yield from _iter_registered_tasks(*module_names)
    else:
        raise ValueError("Class type does not support discovery")


def _iter_registered_tasks(*filter_modules: Iterable[str]) -> Iterable[dict]:
    """Yields all task classes registered in the current process."""
    for cls in Task.get_subclasses():
        module = cls.__module__
        if filter_modules and not any(
            module.startswith(prefix) for prefix in filter_modules
        ):
            continue
        task_identifier = cls.class_registry_name()
        category = task_identifier.split(".")[0]
        yield {
            "task_type": "class",
            "task_identifier": task_identifier,
            "required_input_names": list(cls.required_input_names()),
            "optional_input_names": list(cls.optional_input_names()),
            "output_names": list(cls.output_names()),
            "category": category,
        }


def _iter_method_tasks(
    *module_names: Iterable[str],
    filter_method_name: Optional[Callable[[str], bool]] = None
) -> Iterable[dict]:
    """Yields all task methods from the provided module_names. The module_names will be will
    imported for discovery.
    """
    for module_name in module_names:
        mod = importlib.import_module(module_name)
        for method in inspect.getmembers(mod, inspect.isfunction):
            method_name, method_qn = method
            if filter_method_name and not filter_method_name(method_name):
                continue
            if method_name.startswith("_"):
                continue
            task_identifier = qualname(method_qn)
            category = task_identifier.split(".")[0]
            yield {
                "task_type": "method",
                "task_identifier": qualname(method_qn),
                "category": category,
            }
