import os
import sys

import pytest

from ..task import Task

WIN32 = sys.platform == "win32"


pyscript = r"""
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", type=int, default=0)
    args = parser.parse_args()
    print("input a =", args.a)
    assert args.a == 10
"""


@pytest.mark.parametrize("shebang", [True, False])
@pytest.mark.parametrize("fail", [True, False])
def test_python_script_task(tmp_path, varinfo, shebang, fail):
    if WIN32 and shebang:
        pytest.skip("windows does not have shebangs")

    pyscriptname = tmp_path / "test.py"
    with open(pyscriptname, mode="w") as f:
        if shebang:
            f.write(f"#!{sys.executable}\n")
        f.writelines(pyscript)
    if not WIN32:
        os.chmod(pyscriptname, 0o755)

    if fail:
        a = 11
    else:
        a = 10

    task = Task.instantiate(
        "ScriptExecutorTask",
        inputs={
            "a": a,
            "_script": str(pyscriptname),
            "_capture_output": True,
            "_raise_on_error": False,
        },
        varinfo=varinfo,
    )
    task.execute()
    _assert_outputs(task, a, fail)


if WIN32:
    shellscript = r"""@echo off

set a=0

:initial
if "%1"=="" goto done
echo              %1
set aux=%1
if "%aux:~0,1%"=="-" (
   set varname=%aux:~1,250%
) else (
   set "%varname%=%1"
   set varname=
)
shift
goto initial
:done

echo input a = %a%
if %a%==10 (
    exit 0
) else (
    echo "failure" 1>&2
    exit 1
)
"""
else:
    shellscript = r"""a=0

while getopts u:a:f: flag
do
    case "${flag}" in
        a) a=${OPTARG};;
    esac
done

echo "input a = "$a
if [[ $a == "10" ]]; then
    exit 0
else
    echo "failure" 1>&2
    exit 1
fi
"""


@pytest.mark.parametrize("shebang", [True, False])
@pytest.mark.parametrize("fail", [True, False])
def test_shell_script_task(tmp_path, varinfo, shebang, fail):
    if WIN32:
        if shebang:
            pytest.skip("windows does not have shebangs")
        ext = ".bat"
    else:
        ext = ".sh"
    filename = tmp_path / f"test{ext}"
    with open(filename, mode="w") as f:
        if shebang:
            f.write("#!/bin/bash\n")
        f.writelines(shellscript)
    if not WIN32:
        os.chmod(filename, 0o755)

    if fail:
        a = 11
    else:
        a = 10

    task = Task.instantiate(
        "ScriptExecutorTask",
        inputs={
            "a": a,
            "_script": str(filename),
            "_capture_output": True,
            "_raise_on_error": False,
        },
        varinfo=varinfo,
    )
    task.execute()
    _assert_outputs(task, a, fail)


def test_command_task(tmp_path, varinfo):
    filename = tmp_path / "test.txt"
    with open(filename, mode="w"):
        pass

    task = Task.instantiate(
        "ScriptExecutorTask",
        inputs={
            "0": str(tmp_path),
            "_script": "dir",
            "_capture_output": True,
            "_raise_on_error": False,
        },
        varinfo=varinfo,
    )
    task.execute()
    assert task.done
    assert "test.txt" in task.outputs.out


def _assert_outputs(task, a, fail):
    assert task.done
    out = "".join(task.outputs.out)
    assert f"input a = {a}" in out
    err = "".join(task.outputs.err)
    if fail:
        assert task.outputs.return_code != 0
        assert err
    else:
        assert task.outputs.return_code == 0
        assert not err
