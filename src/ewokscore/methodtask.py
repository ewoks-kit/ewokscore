from typing import Mapping

from ewoksutils.import_utils import import_method

from .task import Task

METHOD_ARGUMENT = "_method"


class MethodExecutorTask(
    Task, input_names=[METHOD_ARGUMENT], output_names=["return_value"]
):
    METHOD_ARGUMENT = METHOD_ARGUMENT

    def _get_task_identifier(self, inputs: Mapping) -> str:
        return inputs.get(self.METHOD_ARGUMENT, self.class_registry_name())

    def run(self):
        kwargs = self.get_named_input_values()
        args = self.get_positional_input_values()
        fullname = kwargs.pop(self.METHOD_ARGUMENT)
        method = import_method(fullname)

        result = method(*args, **kwargs)

        self.outputs.return_value = result
