from time import sleep
from ewokscore.taskwithprogress import TaskWithProgress


class SumList(
    TaskWithProgress,
    input_names=["list"],
    optional_input_names=["delay"],
    output_names=["sum"],
):
    """
    Simple Task processing summation of a list
    """

    def run(self):
        if self.inputs.list is None:
            raise ValueError("list should be provided")
        if self.inputs.delay:
            delay = self.inputs.delay
        else:
            delay = 0
        sum_ = 0
        n_elmt = len(self.inputs.list)
        for i_elmt, elmt in enumerate(self.inputs.list):
            sum_ += elmt
            self.progress = (i_elmt / n_elmt) * 100.0
            sleep(delay)
        self.progress = 100.0
        self.outputs.sum = sum_
