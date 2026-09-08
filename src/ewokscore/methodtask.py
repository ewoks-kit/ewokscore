import dataclasses
import functools
import inspect
import sys
from collections.abc import Mapping
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Type

if sys.version_info < (3, 9):
    from typing_extensions import get_type_hints
else:
    from typing import get_type_hints

from ewoksutils.import_utils import import_method
from pydantic import BaseModel
from pydantic import create_model

from .model import BaseInputModel
from .model import BaseOutputModel
from .task import Task

METHOD_ARGUMENT = "_method"
SINGLE_OUTPUT_NAME = "return_value"

_UNMODELLABLE_KINDS = frozenset(
    {
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.VAR_POSITIONAL,
        inspect.Parameter.VAR_KEYWORD,
    }
)


class MethodExecutorTask(
    Task, input_names=[METHOD_ARGUMENT], output_names=[SINGLE_OUTPUT_NAME]
):
    """Executes the python function provided as the `_method` input."""

    METHOD_ARGUMENT = METHOD_ARGUMENT

    def _warn_unexpected_inputs(self, unexpected_names: Set[str]) -> None:
        pass

    def _get_task_identifier(self, inputs: Mapping) -> str:
        return inputs.get(self.METHOD_ARGUMENT, self.class_registry_name())

    def run(self) -> None:
        kwargs = self.get_named_input_values()
        args = self.get_positional_input_values()
        fullname = kwargs.pop(self.METHOD_ARGUMENT)
        method = import_method(fullname)

        result = method(*args, **kwargs)

        self.outputs[SINGLE_OUTPUT_NAME] = result


class MethodTask(Task, register=False):
    """Executes a python function. Use `get_method_task` to get the task class
    of a specific function.
    """

    _METHOD: Optional[str] = None

    def __init_subclass__(subclass, task_identifier: Optional[str] = None, **kwargs):
        if task_identifier is None:
            super().__init_subclass__(**kwargs)
            return

        method = import_method(task_identifier)
        subclass._METHOD = task_identifier
        super().__init_subclass__(**_task_arguments(method), **kwargs)
        subclass.__doc__ = inspect.getdoc(method)

    def _warn_unexpected_inputs(self, unexpected_names: Set[str]) -> None:
        pass

    def _get_task_identifier(self, inputs: Mapping) -> str:
        return self._METHOD or self.class_registry_name()

    def run(self) -> None:
        method = import_method(self._METHOD)
        args = self.get_positional_input_values()
        kwargs = self.get_named_input_values()

        result = method(*args, **kwargs)

        if self._OUTPUT_MODEL is None:
            self.outputs[SINGLE_OUTPUT_NAME] = result
            return

        for name in self._OUTPUT_MODEL.model_fields:
            if isinstance(result, Mapping):
                self.outputs[name] = result[name]
            else:
                self.outputs[name] = getattr(result, name)


@functools.lru_cache(maxsize=None)
def get_method_task(task_identifier: str) -> Type[MethodTask]:
    """Task class that executes the function with the given qualified name."""

    class GeneratedMethodTask(
        MethodTask, task_identifier=task_identifier, register=False
    ):
        pass

    method_name = task_identifier.rsplit(".", 1)[-1]
    name = "".join(part.title() for part in method_name.split("_")) + "Task"
    GeneratedMethodTask.__name__ = name
    GeneratedMethodTask.__qualname__ = name
    return GeneratedMethodTask


def _task_arguments(method: Callable) -> Dict[str, Any]:
    """Task input and output arguments derived from the signature of `method`."""
    arguments: Dict[str, Any] = dict()

    input_model = _input_model(method)
    if input_model is None:
        arguments.update(_input_arguments(method))
    else:
        arguments["input_model"] = input_model

    output_model = _output_model(method)
    if output_model is None:
        arguments["output_names"] = [SINGLE_OUTPUT_NAME]
    else:
        arguments["output_model"] = output_model

    return arguments


def _type_hints(obj: Any) -> Dict[str, Any]:
    """Type hints of `obj`, empty when an annotation cannot be resolved."""
    try:
        return get_type_hints(obj, include_extras=True)
    except NameError:
        return dict()


def _input_model(method: Callable) -> Optional[Type[BaseInputModel]]:
    """Input model with a field per argument of `method`, or `None` when the
    arguments cannot be expressed as model fields.
    """
    parameters = list(inspect.signature(method).parameters.values())
    if any(parameter.kind in _UNMODELLABLE_KINDS for parameter in parameters):
        return None

    hints = _type_hints(method)
    fields = {
        parameter.name: (
            hints.get(parameter.name, Any),
            (
                ...
                if parameter.default is inspect.Parameter.empty
                else parameter.default
            ),
        )
        for parameter in parameters
    }
    return create_model(
        f"{method.__name__}InputModel", __base__=BaseInputModel, **fields
    )


def _output_model(method: Callable) -> Optional[Type[BaseOutputModel]]:
    """Output model with a field per task output of `method`, or `None` when the
    return type does not define task outputs.
    """
    return_type = _type_hints(method).get("return")
    if not isinstance(return_type, type):
        return None

    if issubclass(return_type, BaseOutputModel):
        return return_type
    if issubclass(return_type, BaseModel):
        return create_model(
            f"{method.__name__}OutputModel", __base__=(BaseOutputModel, return_type)
        )

    names = _output_names(return_type)
    if not names:
        return None

    hints = _type_hints(return_type)
    fields = {name: (hints.get(name, Any), ...) for name in names}
    return create_model(
        f"{method.__name__}OutputModel", __base__=BaseOutputModel, **fields
    )


def _output_names(return_type: Type) -> Tuple[str, ...]:
    """Names of the task outputs defined by a return type."""
    if dataclasses.is_dataclass(return_type):
        return tuple(field.name for field in dataclasses.fields(return_type))
    if issubclass(return_type, tuple) and hasattr(return_type, "_fields"):
        return tuple(return_type._fields)
    if issubclass(return_type, dict):
        # A TypedDict is a dict subclass with annotated keys
        return tuple(_type_hints(return_type))
    return tuple()


def _input_arguments(method: Callable) -> Dict[str, Any]:
    """Task input arguments for the arguments of `method` that cannot be model fields."""
    required: List[str] = list()
    optional: List[str] = list()
    n_required_positional = 0
    for parameter in inspect.signature(method).parameters.values():
        if parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
            # Cannot be a named task input
            if parameter.default is inspect.Parameter.empty:
                n_required_positional += 1
            continue
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if parameter.default is inspect.Parameter.empty:
            required.append(parameter.name)
        else:
            optional.append(parameter.name)

    return {
        "input_names": required,
        "optional_input_names": optional,
        "n_required_positional_inputs": n_required_positional,
    }
