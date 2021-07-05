import sys
import subprocess
from .task import Task


class ScriptExecutorTask(Task, input_names=["script"], output_names=["returncode"]):
    def run(self):
        fullname = self.inputs.script
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
            if k != "script":
                args.extend((argmarker + k, str(v)))
        result = subprocess.run(args)
        # result.check_returncode()
        self.outputs.returncode = result.returncode
