import os
from ewokscore.task import Task

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
    shellscriptname = tmpdir / "test.sh"
    with open(shellscriptname, mode="w") as f:
        f.writelines(shellscript)
    os.chmod(shellscriptname, 0o755)

    task = Task.instantiate(
        "ScriptExecutorTask",
        inputs={"a": 10, "_script": str(shellscriptname)},
        varinfo=varinfo,
    )
    task.execute()
    assert task.done
    assert task.outputs.return_code == 0
    captured = capsys.readouterr()
    # assert captured.out == "10\n"
    assert captured.err == ""
