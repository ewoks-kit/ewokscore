from collections.abc import Sequence, Mapping
import functools
import inspect
from types import FunctionType
from typing import get_type_hints, Optional, Tuple, Union

from ewoksutils.import_utils import import_method

from .task import Task
from .utils import is_namedtuple, method_arguments


def task(
    function: FunctionType,
    output_names: Optional[Union[str, Sequence[str]]] = None,
) -> FunctionType:
    """Function decorator"""
    if isinstance(output_names, str):
        output_names = (output_names,)
    elif output_names is not None:
        output_names = tuple(output_names)

    function._ewoks_output_names = output_names  # noqa
    return function


def _method_output_names(method) -> Tuple[str]:
    sig = inspect.signature(method)
    return_type = sig.return_annotation
    if return_type is None:
        return ()

    if return_type is inspect.Signature.empty or not inspect.isclass(return_type):
        return ("return_value",)

    return_annotations = get_type_hints(return_type)
    if return_annotations:
        return tuple(return_annotations.keys())

    if is_namedtuple(return_type):
        return tuple(return_type._fields)

    return ("return_value",)


class MethodExecutorTask(Task):

    def __init_subclass__(
        cls,
        task_identifier: str,
        output_names: Optional[Union[str, Sequence[str]]] = None,
        **kwargs,
    ):
        cls._TASK_IDENTIFIER = task_identifier

        method = import_method(task_identifier)
        input_names, optional_input_names = method_arguments(method)

        if isinstance(output_names, str):
            output_names = [output_names]

        if output_names is None:
            if hasattr(method, "_ewoks_output_names"):
                output_names = method._ewoks_output_names
            if output_names is None:
                output_names = _method_output_names(method)

        super().__init_subclass__(
            input_names=input_names,
            optional_input_names=optional_input_names,
            output_names=output_names,
            **kwargs,
        )
        cls.__doc__ = inspect.getdoc(method)

    def run(self):
        kwargs = self.get_named_input_values()
        args = self.get_positional_input_values()

        method = import_method(self._TASK_IDENTIFIER)

        result = method(*args, **kwargs)

        output_names = tuple(self.output_names())
        if len(output_names) == 0:
            return

        if len(output_names) == 1:
            self.outputs[output_names[0]] = result
            return

        if isinstance(result, Mapping):
            for name in output_names:
                if name in result:
                    self.outputs[name] = result[name]
            return

        for name in output_names:
            if hasattr(result, name):
                self.outputs[name] = getattr(result, name)


@functools.lru_cache()
def get_method_task(task_identifier: str) -> MethodExecutorTask:
    class MethodTask(MethodExecutorTask, task_identifier=task_identifier):
        pass

    return MethodTask
