from .examples.tasks.sumlist import SumList
from ewokscore.progress import TextProgress
import numpy.random


def test_task_progress(capsys, varinfo):
    # case 1: no TextProgress is provided
    task = SumList(
        inputs={"list": numpy.random.random(10000)},
        varinfo=varinfo,
    )
    assert not task.done
    task.execute()
    stdout = capsys.readouterr()
    assert len(stdout.out) == 0
    assert task.done

    # case 2: TextProgress is provided
    task = SumList(
        inputs={"list": numpy.random.random(10000)},
        varinfo=varinfo,
        progress=TextProgress(name="SumList"),
    )
    assert not task.done
    task.execute()
    stdout = capsys.readouterr()
    assert len(stdout.out) > 0
    assert stdout.out.count("DONE") > 0
    assert task.done
