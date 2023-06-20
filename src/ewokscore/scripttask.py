import os
import sys
import subprocess
from .task import Task

SCRIPT_ARGUMENT = "_script"
WIN32 = sys.platform == "win32"


class ScriptExecutorTask(
    Task,
    input_names=[SCRIPT_ARGUMENT],
    optional_input_names=["_capture_output", "_merge_err", "_raise_on_error"],
    output_names=["return_code", "out", "err"],
):
    SCRIPT_ARGUMENT = SCRIPT_ARGUMENT

    def run(self):
        fullname = self.inputs._script
        if not isinstance(fullname, str):
            raise TypeError(fullname, type(fullname))

        # Python or shell script
        is_python = fullname.endswith(".py")

        # Is script executable?
        if os.path.isfile(fullname):
            # existing python or shell script
            fullname = os.path.abspath(fullname)
            if WIN32:
                is_executable = not is_python
            else:
                with open(fullname, "r") as f:
                    is_executable = f.readline().startswith("#!")
        else:
            # command (although it could be a script that does not exist)
            is_executable = True
            fullname = fullname.split(" ")

        # Select executable when fullname itself is not executable
        executable = None
        if not is_executable:
            if is_python:
                executable = sys.executable
            elif not WIN32:
                executable = "bash"

        # Command starts with "[executable] fullname ..."
        cmd = []
        if executable:
            cmd.append(executable)
        if isinstance(fullname, str):
            cmd.append(fullname)
        else:
            cmd.extend(fullname)

        # Script/command arguments
        if is_python:
            # Use full parameter name
            argmarker = "--"
        else:
            # Use getopts-style parameter parsing by the script
            argmarker = "-"
        skip = self.input_names()
        for k, v in self.get_input_values().items():
            if k not in skip:
                cmd.extend((argmarker + k, str(v)))

        # Run
        stdout = stderr = None
        if self.inputs._capture_output:
            stdout = subprocess.PIPE
            if self.inputs._merge_err:
                stderr = subprocess.STDOUT
            else:
                stderr = subprocess.PIPE

        result = subprocess.run(cmd, cwd=os.getcwd(), stdout=stdout, stderr=stderr)
        if self.inputs._raise_on_error:
            result.check_returncode()

        self.outputs.return_code = result.returncode
        if result.stdout:
            self.outputs.out = result.stdout.decode()
        elif self.inputs._capture_output:
            self.outputs.out = ""
        else:
            self.outputs.out = None
        if result.stderr:
            self.outputs.err = result.stderr.decode()
        elif self.inputs._capture_output and not self.inputs._merge_err:
            self.outputs.err = ""
        else:
            self.outputs.err = None
