from time import sleep
from ewokscore import Task


class SumTask(
    Task,
    input_names=["a"],
    optional_input_names=["b", "delay"],
    output_names=["result"],
):
    def run(self):
        result = self.inputs.a
        if self.inputs.b:
            result += self.inputs.b
        if self.inputs.delay:
            sleep(self.inputs.delay)
        self.outputs.result = result
