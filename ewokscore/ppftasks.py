from .task import Task
from .utils import import_method


class PpfMethodExecutorTask(
    Task,
    input_names=["method"],
    optional_input_names=["ppfdict"],
    output_names=["ppfdict"],
):
    """Ppf workflows pass one dictionary around between tasks and this dictionary
    gets updates by each task. This dictionary is unpacked into the unexpected
    arguments and passed to the method.
    """

    def run(self):
        method_kwargs = self.input_values
        fullname = method_kwargs.pop("method")
        method = import_method(fullname)
        ppfdict = method_kwargs.pop("ppfdict", None)
        if ppfdict:
            method_kwargs.update(ppfdict)

        result = method(**method_kwargs)

        method_kwargs.update(result)
        self.outputs.ppfdict = method_kwargs


class PpfPortTask(
    Task, optional_input_names=["ppfdict", "ppfport"], output_names=["ppfdict"]
):
    """A ppfmethod which represents the identity mapping"""

    def run(self):
        method_kwargs = self.input_values
        method_kwargs.pop("ppfport")  # not used
        ppfdict = method_kwargs.pop("ppfdict", None)
        if ppfdict:
            method_kwargs.update(ppfdict)

        self.outputs.ppfdict = method_kwargs
