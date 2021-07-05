from .task import Task
from .utils import import_method


class MethodExecutorTask(Task, input_names=["method"], output_names=["return_value"]):
    def run(self):
        kwargs = self.named_input_values
        args = self.positional_input_values
        fullname = kwargs.pop("method")
        method = import_method(fullname)

        result = method(*args, **kwargs)

        self.outputs.return_value = result
