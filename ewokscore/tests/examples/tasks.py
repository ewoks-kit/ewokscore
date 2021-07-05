from ewokscore import Task


__all__ = ["SumTask", "CondSumTask"]


class SumTask(
    Task, input_names=["a"], optional_input_names=["b"], output_names=["result"]
):
    def run(self):
        result = self.inputs.a
        if self.inputs.b:
            result += self.inputs.b
        self.outputs.result = result


class CondSumTask(SumTask, output_names=["too_small"]):
    def run(self):
        super().run()
        self.outputs.too_small = self.outputs.result < 10


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
