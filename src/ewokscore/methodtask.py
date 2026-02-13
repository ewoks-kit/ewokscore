from collections.abc import Mapping
import functools
import inspect
from types import FunctionType
from typing import get_type_hints, Set

from ewoksutils.import_utils import import_method

from .task import Task
from .utils import is_namedtuple, method_arguments


def task_outputs(function: FunctionType) -> FunctionType:
    """Function decorator so ewoks extracts task outputs from return type elements/attributes"""
    # Report error early
    if not _method_output_names(function):
        raise ValueError("Function return type does not define any output name")

    function._ewoks_unpack_outputs = True  # noqa
    return function


def _method_output_names(method) -> Set[str]:
    sig = inspect.signature(method)
    return_type = sig.return_annotation
    if return_type is inspect.Signature.empty or not inspect.isclass(return_type):
        return set()

    return_annotations = get_type_hints(return_type)
    if return_annotations:
        return set(return_annotations.keys())

    if is_namedtuple(return_type):
        return set(return_type._fields)

    return set()


class MethodExecutorTask(Task):
    _METHOD_REQUIRED_INPUTS = tuple()
    _METHOD_OPTIONAL_INPUTS = tuple()
    _METHOD_UNPACK_OUTPUTS = False

    def __init_subclass__(cls, task_identifier: str):
        cls._TASK_IDENTIFIER = task_identifier

        method = import_method(task_identifier)
        cls._METHOD_REQUIRED_INPUTS, cls._METHOD_OPTIONAL_INPUTS = method_arguments(
            method
        )

        cls._METHOD_UNPACK_OUTPUTS = getattr(method, "_ewoks_unpack_outputs", False)
        if cls._METHOD_UNPACK_OUTPUTS:
            output_names = _method_output_names(method)
            if not output_names:
                raise RuntimeError(
                    f"{task_identifier}'s return type do not define any output name"
                )
        else:
            output_names = ["return_value"]

        super().__init_subclass__(
            # required inputs are optional to support passing them as positional inputs
            optional_input_names=cls._METHOD_REQUIRED_INPUTS
            + cls._METHOD_OPTIONAL_INPUTS,
            output_names=output_names,
        )
        cls.__doc__ = inspect.getdoc(method)

    # Advertise effective method required/optional input names
    # rather than the less constrained task ones

    @classmethod
    def required_input_names(cls):
        return cls._METHOD_REQUIRED_INPUTS

    @classmethod
    def optional_input_names(cls):
        return cls._METHOD_OPTIONAL_INPUTS

    def run(self):
        kwargs = self.get_named_input_values()
        args = self.get_positional_input_values()

        method = import_method(self._TASK_IDENTIFIER)

        result = method(*args, **kwargs)

        if not self._METHOD_UNPACK_OUTPUTS:
            self.outputs.return_value = result
            return

        if isinstance(result, Mapping):
            for name in self.output_names():
                if name in result:
                    self.outputs[name] = result[name]
            return

        for name in self.output_names():
            if hasattr(result, name):
                self.outputs[name] = getattr(result, name)


@functools.lru_cache()
def get_method_task(task_identifier: str) -> MethodExecutorTask:
    class MethodTask(MethodExecutorTask, task_identifier=task_identifier):
        pass

    return MethodTask
