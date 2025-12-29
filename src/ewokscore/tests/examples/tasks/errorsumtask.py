from ....task import Task


class ErrorSumTask(
    Task, optional_input_names=["a", "b", "raise_error"], output_names=["result"]
):
    """Add two number with intentional exception"""

    def run(self):
        result = self.get_input_value("a", default=0)
        if self.inputs.b:
            result += self.inputs.b
        self.outputs.result = result
        if self.inputs.raise_error:
            raise RuntimeError("Intentional error")
