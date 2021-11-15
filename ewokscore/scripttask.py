import sys
import subprocess
from .task import Task

SCRIPT_ARGUMENT = "_script"


class ScriptExecutorTask(
    Task, input_names=[SCRIPT_ARGUMENT], output_names=["return_code"]
):
    SCRIPT_ARGUMENT = SCRIPT_ARGUMENT

    def run(self):
        fullname = self.inputs._script
        if not isinstance(fullname, str):
            raise TypeError(fullname, type(fullname))
        args = []
        if fullname.endswith(".py"):
            argmarker = "--"
            args.append(sys.executable)
        else:
            argmarker = "-"
            args.append("bash")
        args.append(fullname)
        for k, v in self.input_values.items():
            if k != self.SCRIPT_ARGUMENT:
                args.extend((argmarker + k, str(v)))
        result = subprocess.run(args)
        # result.check_returncode()
        self.outputs.return_code = result.returncode
