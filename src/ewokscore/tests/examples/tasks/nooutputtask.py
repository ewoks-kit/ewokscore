from pprint import pformat as _pformat  # hide from task discovery

from ....task import Task


class NoOutputTask(Task):
    """A task without outputs"""

    def run(self):
        input_values = self.get_input_values()
        if input_values:
            print(f"{self.label}: {_pformat(input_values)}")
        else:
            print(f"{self.label}: <no inputs>")
