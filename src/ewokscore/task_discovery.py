import inspect
import logging
import pkgutil
import sys
from fnmatch import fnmatch
from types import FunctionType
from types import ModuleType
from typing import Generator
from typing import List
from typing import Optional
from typing import TypedDict

from ewoksutils.import_utils import import_module
from ewoksutils.import_utils import qualname

from .entry_points import entry_points
from .task import Task


class _TaskInputs(TypedDict):
    required_input_names: List[str]
    optional_input_names: List[str]
    n_required_positional_inputs: int


class _CommonTaskFields(_TaskInputs):
    task_identifier: str
    output_names: List[str]
    category: str
    description: Optional[str]
    input_model: Optional[str]
    output_model: Optional[str]


class TaskDict(_CommonTaskFields):
    task_type: str


logger = logging.getLogger(__name__)


def discover_tasks_from_modules(
    *module_names_or_patterns: str,
    task_type: Optional[str] = None,
    reload: bool = False,
    raise_import_failure: bool = True,
) -> List[TaskDict]:
    if task_type is None:
        task_types = ("class", "ppfmethod", "method")
    else:
        task_types = (task_type,)

    result = list()
    for task_type in task_types:
        # Module names can contain patterns
        for module_name_or_pattern in module_names_or_patterns:
            for module_name in _iter_modules_from_pattern(
                module_name_or_pattern,
                reload=reload,
                raise_import_failure=raise_import_failure,
            ):

                result.extend(
                    _iter_discover_tasks_from_modules(
                        module_name,
                        task_type=task_type,
                        reload=reload,
                        raise_import_failure=raise_import_failure,
                    )
                )

    return result


def _iter_discover_tasks_from_modules(
    *module_names: str,
    task_type: str,
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
        raise ValueError(f"Task type {task_type} does not support discovery")


def _iter_registered_tasks(*filter_modules: str) -> Generator[TaskDict, None, None]:
    """Yields all task classes registered in the current process."""
    for cls in Task.get_subclasses():
        assert issubclass(cls, Task)
        module = cls.__module__
        if filter_modules and not any(
            module.startswith(prefix) for prefix in filter_modules
        ):
            continue

        task_identifier = cls.class_registry_name()
        if task_identifier is None:
            # Exclude unregistered tasks
            continue

        category = task_identifier.split(".")[0]
        name = task_identifier.split(".")[-1]
        if name.startswith("_"):
            # Exclude hidden tasks
            continue

        input_model = cls.input_model()
        output_model = cls.output_model()
        yield {
            "task_type": "class",
            "task_identifier": task_identifier,
            "required_input_names": sorted(cls.required_input_names()),
            "optional_input_names": sorted(cls.optional_input_names()),
            "output_names": sorted(cls.output_names()),
            "category": category,
            "description": cls.__doc__,
            "input_model": qualname(input_model) if input_model else None,
            "output_model": qualname(output_model) if output_model else None,
            "n_required_positional_inputs": cls.n_required_positional_inputs(),
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


def _iter_discover_all_tasks(
    reload: bool = False,
    task_type: Optional[str] = None,
    raise_import_failure: bool = False,
) -> Generator[TaskDict, None, None]:
    visited = set()
    if task_type is None:
        task_types = ("class", "ppfmethod", "method")
    else:
        task_types = (task_type,)

    for task_type in task_types:
        group = "ewoks.tasks." + task_type
        for entrypoint in entry_points(group):
            module_pattern = entrypoint.name
            if module_pattern is visited:
                continue
            visited.add(module_pattern)
            yield from discover_tasks_from_modules(
                module_pattern,
                task_type=task_type,
                reload=reload,
                raise_import_failure=raise_import_failure,
            )


def discover_all_tasks(
    reload: bool = False,
    task_type: Optional[str] = None,
    raise_import_failure: bool = False,
) -> List[TaskDict]:
    return list(
        _iter_discover_all_tasks(
            reload=reload,
            task_type=task_type,
            raise_import_failure=raise_import_failure,
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


def _method_arguments(method) -> _TaskInputs:
    sig = inspect.signature(method)
    required_input_names: List[str] = list()
    optional_input_names: List[str] = list()
    n_required_positional_inputs = 0

    for name, param in sig.parameters.items():
        if param.kind == param.POSITIONAL_ONLY:
            n_required_positional_inputs += 1
            continue
        if param.kind == param.VAR_POSITIONAL:
            continue
        if param.kind == param.VAR_KEYWORD:
            continue

        required = param.default is inspect._empty
        if required:
            required_input_names.append(name)
        else:
            optional_input_names.append(name)

    return {
        "required_input_names": required_input_names,
        "optional_input_names": optional_input_names,
        "n_required_positional_inputs": n_required_positional_inputs,
    }


def _common_method_task_fields(
    method_name: str, method_qn: FunctionType, mod: ModuleType
) -> _CommonTaskFields:

    task_identifier = qualname(method_qn)
    method = getattr(mod, method_name)

    return {
        **_method_arguments(method),
        "task_identifier": qualname(method_qn),
        "output_names": ["return_value"],
        "category": task_identifier.split(".")[0],
        "description": method.__doc__,
        "input_model": None,
        "output_model": None,
    }
