import sys
import pkgutil
import inspect
import logging
from fnmatch import fnmatch
from types import FunctionType, ModuleType
from typing import Generator, Optional, List, Dict, Tuple, Union

if sys.version_info < (3, 9):
    from importlib_metadata import entry_points as _entry_points

    def iter_entry_points(group: str):
        return _entry_points(group=group)

elif sys.version_info < (3, 10):
    from importlib.metadata import entry_points as _entry_points

    def iter_entry_points(group: str):
        return _entry_points().get(group, [])

else:
    from importlib.metadata import entry_points as _entry_points

    def iter_entry_points(group: str):
        return _entry_points(group=group)


from ewoksutils.import_utils import qualname
from ewoksutils.import_utils import import_module

from .task import Task

TaskDict = Dict[str, Union[str, List[str]]]


logger = logging.getLogger(__name__)


def discover_tasks_from_modules(
    *module_names: str,
    task_type="class",
    reload: bool = False,
    raise_import_failure: bool = True,
) -> List[TaskDict]:
    return list(
        iter_discover_tasks_from_modules(
            *module_names,
            task_type=task_type,
            reload=reload,
            raise_import_failure=raise_import_failure,
        )
    )


def iter_discover_tasks_from_modules(
    *module_names: str,
    task_type="class",
    reload: bool = False,
    raise_import_failure: bool = True,
) -> Generator[TaskDict, None, None]:
    if "" not in sys.path:
        # This happens when the python process was launched
        # through a python console script
        sys.path.append("")

    if task_type == "method":
        yield from _iter_method_tasks(
            *module_names, reload=reload, raise_import_failure=raise_import_failure
        )
    elif task_type == "ppfmethod":
        yield from _iter_ppfmethod_tasks(
            *module_names, reload=reload, raise_import_failure=raise_import_failure
        )
    elif task_type == "class":
        for module_name in module_names:
            _safe_import_module(
                module_name, reload=reload, raise_import_failure=raise_import_failure
            )
        yield from _iter_registered_tasks(*module_names)
    else:
        raise ValueError("Class type does not support discovery")


def _iter_registered_tasks(*filter_modules: str) -> Generator[TaskDict, None, None]:
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
            "description": cls.__doc__,
        }


def _iter_method_tasks(
    *module_names: str,
    reload: bool = False,
    raise_import_failure: bool = False,
) -> Generator[TaskDict, None, None]:
    """Yields all task methods from the provided module_names. The module_names will be will
    imported for discovery.
    """
    for module_name in module_names:
        mod = _safe_import_module(
            module_name, reload=reload, raise_import_failure=raise_import_failure
        )
        if mod is None:
            continue
        for method_name, method_qn in inspect.getmembers(mod, inspect.isfunction):
            if method_name.startswith("_"):
                continue

            yield {
                "task_type": "method",
                **_common_method_task_fields(method_name, method_qn, mod),
            }


def _iter_ppfmethod_tasks(
    *module_names: str,
    reload: bool = False,
    raise_import_failure: bool = False,
) -> Generator[TaskDict, None, None]:
    """Yields all task ppfmethods from the provided module_names. The module_names will be will
    imported for discovery.

    The difference with regular methods is that ppfmethods are expected to be called `run`. Other method names will be ignored.
    """
    for module_name in module_names:
        mod = _safe_import_module(
            module_name, reload=reload, raise_import_failure=raise_import_failure
        )
        if mod is None:
            continue
        for method_name, method_qn in inspect.getmembers(mod, inspect.isfunction):
            if method_name != "run":
                continue

            yield {
                "task_type": "ppfmethod",
                **_common_method_task_fields(method_name, method_qn, mod),
            }


def iter_discover_all_tasks(
    reload: bool = False, raise_import_failure: bool = False
) -> Generator[TaskDict, None, None]:
    visited = set()
    for task_type in ("class", "ppfmethod", "method"):
        group = "ewoks.tasks." + task_type
        for entrypoint in iter_entry_points(group):
            module_pattern = entrypoint.name
            if module_pattern is visited:
                continue
            visited.add(module_pattern)
            for module_name in _iter_modules_from_pattern(
                module_pattern, reload=reload, raise_import_failure=raise_import_failure
            ):
                yield from iter_discover_tasks_from_modules(
                    module_name,
                    task_type=task_type,
                    reload=reload,
                    raise_import_failure=raise_import_failure,
                )


def discover_all_tasks(
    reload: bool = False, raise_import_failure: bool = False
) -> List[TaskDict]:
    return list(
        iter_discover_all_tasks(
            reload=reload, raise_import_failure=raise_import_failure
        )
    )


def _iter_modules_from_pattern(
    module_pattern: str, reload: bool = False, raise_import_failure: bool = False
) -> Generator[str, None, None]:
    if "*" not in module_pattern:
        yield module_pattern
        return
    ndots = module_pattern.count(".")
    parts = module_pattern.split(".")
    pkg = _safe_import_module(
        parts[0], reload=reload, raise_import_failure=raise_import_failure
    )
    if pkg is None:
        return
    if raise_import_failure:

        def onerror(module_name):
            raise

    else:
        onerror = _onerror
    for pkginfo in pkgutil.walk_packages(
        pkg.__path__, pkg.__name__ + ".", onerror=onerror
    ):
        if pkginfo.name.count(".") == ndots and fnmatch(pkginfo.name, module_pattern):
            yield pkginfo.name


def _safe_import_module(
    module_name: str, reload: bool = False, raise_import_failure: bool = False
) -> Optional[ModuleType]:
    try:
        return import_module(module_name, reload=reload)
    except Exception as e:
        if raise_import_failure:
            raise
        _onerror(module_name, exception=e)


def _onerror(module_name, exception: Optional[Exception] = None):
    if exception is None:
        exception = sys.exc_info()[1]
    logger.error(f"Module '{module_name}' cannot be imported: {exception}")


def _method_arguments(method) -> Tuple[List[str], List[str]]:
    sig = inspect.signature(method)
    required_input_names = list()
    optional_input_names = list()
    for name, param in sig.parameters.items():
        required = param.default is inspect._empty
        if param.kind == param.VAR_POSITIONAL:
            continue
        if param.kind == param.VAR_KEYWORD:
            continue
        if required:
            required_input_names.append(name)
        else:
            optional_input_names.append(name)
    return required_input_names, optional_input_names


def _common_method_task_fields(
    method_name: str, method_qn: FunctionType, mod: ModuleType
) -> Dict[str, Union[str, List[str]]]:

    task_identifier = qualname(method_qn)
    method = getattr(mod, method_name)
    required_input_names, optional_input_names = _method_arguments(method)

    return {
        "task_identifier": qualname(method_qn),
        "required_input_names": required_input_names,
        "optional_input_names": optional_input_names,
        "output_names": ["return_value"],
        "category": task_identifier.split(".")[0],
        "description": method.__doc__,
    }
