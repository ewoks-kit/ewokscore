from typing import Mapping

from ewoksutils.import_utils import import_method

from .task import Task

METHOD_ARGUMENT = "_method"
PPF_DICT_ARGUMENT = "_ppfdict"


class PpfMethodExecutorTask(
    Task,
    input_names=[METHOD_ARGUMENT],
    optional_input_names=[PPF_DICT_ARGUMENT],
    output_names=[PPF_DICT_ARGUMENT],
):
    """Ppf workflows pass one dictionary around between tasks and this dictionary
    gets updates by each task. This dictionary is unpacked into the unexpected
    arguments and passed to the method.
    """

    METHOD_ARGUMENT = METHOD_ARGUMENT
    PPF_DICT_ARGUMENT = PPF_DICT_ARGUMENT

    def _get_task_identifier(self, inputs: Mapping) -> str:
        return inputs.get(self.METHOD_ARGUMENT, self.class_registry_name())

    def run(self):
        method_kwargs = self.get_input_values()
        fullname = method_kwargs.pop(self.METHOD_ARGUMENT)
        method = import_method(fullname)
        ppfdict = method_kwargs.pop(self.PPF_DICT_ARGUMENT, None)
        if ppfdict:
            method_kwargs.update(ppfdict)

        result = method(**method_kwargs)

        method_kwargs.update(result)
        self.outputs._ppfdict = method_kwargs


class PpfPortTask(
    Task, optional_input_names=[PPF_DICT_ARGUMENT], output_names=[PPF_DICT_ARGUMENT]
):
    """A ppfmethod which represents the identity mapping"""

    PPF_DICT_ARGUMENT = PPF_DICT_ARGUMENT

    def _get_task_identifier(self, inputs: Mapping) -> str:
        return ""

    def run(self):
        method_kwargs = self.get_input_values()
        ppfdict = method_kwargs.pop(self.PPF_DICT_ARGUMENT, None)
        if ppfdict:
            method_kwargs.update(ppfdict)
        self.outputs._ppfdict = method_kwargs
