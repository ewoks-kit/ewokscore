from .sumtask import SumTask


class CondSumTask(SumTask, output_names=["too_small"]):
    def run(self):
        super().run()
        self.outputs.too_small = self.outputs.result < 10
