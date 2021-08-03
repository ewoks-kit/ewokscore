from ewokscore.taskwithprogress import TaskWithProgress


class SumList(TaskWithProgress, input_names=["list"], output_names=["sum"]):
    """
    Simple Task processing summation of a list
    """

    def run(self):
        if self.inputs.list is None:
            raise ValueError("list should be provided")
        sum_ = 0
        n_elmt = len(self.inputs.list)
        for i_elmt, elmt in enumerate(self.inputs.list):
            sum_ += elmt
            self.progress = (i_elmt / n_elmt) * 100.0
        self.progress = 100.0
        self.outputs.sum = sum_
