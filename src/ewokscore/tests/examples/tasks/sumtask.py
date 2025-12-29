from time import sleep as _sleep  # hide from task discovery

from ....taskwithprogress import TaskWithProgress


class SumTask(
    TaskWithProgress,
    input_names=["a"],
    optional_input_names=["b", "delay"],
    output_names=["result"],
):
    """Add two numbers with a delay"""

    def run(self):
        result = self.inputs.a
        if self.inputs.b:
            result += self.inputs.b
        self.progress = 0
        if self.inputs.delay:
            dt = self.inputs.delay / 100
            for i in range(100):
                _sleep(dt)
                self.progress = i + 1
        else:
            self.progress = 100
        self.outputs.result = result
