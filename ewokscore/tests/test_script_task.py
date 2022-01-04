import os
import sys
from ewokscore.task import Task

WIN32 = sys.platform == "win32"


pyscript = r"""
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", type=int, default=0)
    args = parser.parse_args()
    print("input a =", args.a)
    assert args.a == 10
"""


def test_python_script_task(tmpdir, varinfo, capsys):
    pyscriptname = tmpdir / "test.py"
    with open(pyscriptname, mode="w") as f:
        f.writelines(pyscript)

    task = Task.instantiate(
        "ScriptExecutorTask",
        inputs={"a": 10, "_script": str(pyscriptname)},
        varinfo=varinfo,
    )
    task.execute()
    assert task.done
    assert task.outputs.return_code == 0
    captured = capsys.readouterr()
    # assert captured.out == "10\n"
    assert captured.err == ""


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
    echo exit 0
) else (
    echo exit 1
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
    exit 1
fi
"""


def test_shell_script_task(tmpdir, varinfo, capsys):
    if WIN32:
        ext = ".bat"
    else:
        ext = ".sh"
    filename = tmpdir / f"test{ext}"
    with open(filename, mode="w") as f:
        f.writelines(shellscript)
    if not WIN32:
        os.chmod(filename, 0o755)

    task = Task.instantiate(
        "ScriptExecutorTask",
        inputs={"a": 10, "_script": str(filename)},
        varinfo=varinfo,
    )
    task.execute()
    assert task.done
    assert task.outputs.return_code == 0
    captured = capsys.readouterr()
    # assert captured.out == "10\n"
    assert captured.err == ""
