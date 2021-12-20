from pprint import pformat
from ewokscore import Task


class NoOutputTask(Task):
    def run(self):
        input_values = self.input_values
        if input_values:
            print(f"{self.label}: {pformat(input_values)}")
        else:
            print(f"{self.label}: <no inputs>")
