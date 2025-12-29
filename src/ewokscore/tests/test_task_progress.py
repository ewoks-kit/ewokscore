import logging

import numpy.random

from ..events import job_context
from ..events import workflow_context
from ..progress import TextProgress
from .examples.tasks.sumlist import SumList


def test_no_progress_stdout(capsys):
    task = SumList(
        inputs={"list": numpy.random.random(10000)},
    )
    assert not task.done
    task.execute()
    stdout = capsys.readouterr()
    assert len(stdout.out) == 0
    assert task.done


def test_text_progress_stdout(capsys):
    task = SumList(
        inputs={"list": numpy.random.random(10000)},
        progress=TextProgress(name="SumList"),
    )
    assert not task.done
    task.execute()
    stdout = capsys.readouterr()
    assert len(stdout.out) > 0
    assert stdout.out.count("DONE") > 0
    assert task.done


def test_no_progress_events(caplog):
    with caplog.at_level(logging.INFO):
        with job_context(None) as execinfo:
            with workflow_context(execinfo) as execinfo:
                task = SumList(
                    inputs={"list": numpy.random.random(10000)},
                    node_id="node_id",
                    execinfo=execinfo,
                )
                task.execute()
    assert len(caplog.records) == 6


def test_text_progress_events(caplog):
    with caplog.at_level(logging.INFO):
        with job_context(None) as execinfo:
            with workflow_context(execinfo) as execinfo:
                task = SumList(
                    inputs={"list": numpy.random.random(10000)},
                    progress=TextProgress(name="SumList"),
                    node_id="node_id",
                    execinfo=execinfo,
                )
                task.execute()
    nprogress = 100
    assert len(caplog.records) == (nprogress + 6)
    progress = [
        record.progress for record in caplog.records if record.type == "progress"
    ]
    assert len(progress) == nprogress
    assert progress == list(range(1, nprogress + 1))
