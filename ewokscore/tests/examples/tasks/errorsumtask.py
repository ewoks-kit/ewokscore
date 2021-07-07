from ewokscore import Task


class ErrorSumTask(
    Task, optional_input_names=["a", "b", "raise_error"], output_names=["result"]
):
    def run(self):
        result = self.inputs.a
        if result is self.MISSING_DATA:
            result = 0
        if self.inputs.b:
            result += self.inputs.b
        self.outputs.result = result
        if self.inputs.raise_error:
            raise RuntimeError("Intentional error")
