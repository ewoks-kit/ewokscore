from .sumtask import SumTask


class CondSumTask(SumTask, output_names=["too_small"]):
    """Check whether a value is too small"""

    def run(self):
        super().run()
        self.outputs.too_small = self.outputs.result < 10
