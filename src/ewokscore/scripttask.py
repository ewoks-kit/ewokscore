import logging
import os
import subprocess
import sys
from typing import Mapping

from .task import Task

SCRIPT_ARGUMENT = "_script"
WIN32 = sys.platform == "win32"


logger = logging.getLogger(__name__)


class ScriptExecutorTask(
    Task,
    input_names=[SCRIPT_ARGUMENT],
    optional_input_names=["_capture_output", "_merge_err", "_raise_on_error"],
    output_names=["return_code", "out", "err"],
):
    """Task wrapper for a shell command or script.

    When the :code:`SCRIPT_ARGUMENT` input variable is not an existing file, it is assumed to be a command.

    When it is a file, it is assumed to be executable when

    - Windows: it does not have the `".py"` file name extension
    - Linux/Mac: the content does not start with a shebang "#!"

    When the file is not executable a command is prepended

    - :code:`sys.executable` when the file name has the `".py"` extension
    - :code:`bash` otherwise

    Examples of different types of command line arguments

    - **Single-character argument names**:

        .. code-block:: bash

            python -c "print('hello')"

        .. code-block:: python

            inputs = {SCRIPT_ARGUMENT: "python", "c": "print('hello')"}

    - **Arguments without a value**:

        .. code-block:: bash

            ls -a

        .. code-block:: python

            inputs = {SCRIPT_ARGUMENT: "ls", "a": ""}

    - **Multi-character argument names**:

        .. code-block:: bash

            ls --all

        .. code-block:: python

            inputs = {SCRIPT_ARGUMENT: "ls", "all": ""}

    - **Arguments without a name**:

        .. code-block:: bash

            ls .

        .. code-block:: python

            inputs = {SCRIPT_ARGUMENT: "ls", 0: "."}

    - **Merged single-character argument names**:

        .. code-block:: bash

            ls -ltrh

        Since we need `-ltrh` instead of `--ltrh` we can specify
        it as a positional argument

        .. code-block:: python

            inputs = {SCRIPT_ARGUMENT: "ls", 0: "-ltrh"}
    """

    SCRIPT_ARGUMENT = SCRIPT_ARGUMENT

    def _get_task_identifier(self, inputs: Mapping) -> str:
        return inputs.get(self.SCRIPT_ARGUMENT, self.class_registry_name())

    def run(self):
        fullname = self.inputs._script
        if not isinstance(fullname, str):
            raise TypeError(fullname, type(fullname))

        # Is script?
        if os.path.isfile(fullname):
            # existing python or shell script
            is_python = fullname.endswith(".py")
            fullname = os.path.abspath(fullname)
            if WIN32:
                # Assume all non-python scripts are executable
                is_executable = not is_python
            else:
                # Scripts with a shebang are executable
                with open(fullname, "r") as f:
                    is_executable = f.readline().startswith("#!")
        else:
            # command (although it could be a script that does not exist)
            is_python = False
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
        skip = self.input_names()
        positional = list()
        for k, v in self.get_input_values().items():
            if k in skip:
                continue
            value = str(v)
            if isinstance(k, int):
                positional.append((k, value))
                continue
            else:
                if len(k) == 1:
                    argmarker = "-"
                else:
                    argmarker = "--"
                if value:
                    cmd.extend((argmarker + k, value))
                else:
                    cmd.append(argmarker + k)
        cmd.extend([v for _, v in sorted(positional)])

        logger.debug("Command: '%s'", " ".join(cmd))

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
