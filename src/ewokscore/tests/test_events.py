import logging
from contextlib import contextmanager
from logging.handlers import QueueHandler
from queue import Empty
from queue import Queue

import pytest

from .. import events


@contextmanager
def capture_events(blocking):
    queue = Queue()
    handler = QueueHandler(queue)
    events.add_handler(handler, blocking)

    def get_event():
        try:
            return queue.get(block=blocking, timeout=1)
        except Empty:
            raise RuntimeError("event not received by handler") from None

    try:
        yield get_event
    finally:
        events.cleanup()


@pytest.mark.parametrize("blocking", [False, True])
def test_workflow_event(blocking):
    execinfo = {
        "job_id": None,
        "host_name": None,
        "user_name": None,
        "process_id": None,
        "workflow_id": None,
    }
    with capture_events(blocking) as get_event:
        events.send_workflow_event(execinfo=execinfo, event="start")
        event = get_event()
        assert event.type == "start"

        events.send_workflow_event(execinfo=execinfo, event="end", error_message="abc")
        event = get_event()
        assert event.type == "end"
        assert event.error
        assert event.error_message == "abc"


@pytest.mark.parametrize("blocking", [False, True])
def test_task_event(blocking):
    execinfo = {
        "job_id": None,
        "host_name": None,
        "user_name": None,
        "process_id": None,
        "workflow_id": None,
        "node_id": None,
        "task_id": None,
    }
    with capture_events(blocking) as get_event:
        events.send_task_event(
            execinfo=execinfo,
            event="start",
        )
        event = get_event()
        assert event.type == "start"

        events.send_task_event(
            execinfo=execinfo,
            event="progress",
            progress=50,
        )
        event = get_event()
        assert event.type == "progress"
        assert event.progress == 50

        events.send_task_event(
            execinfo=execinfo,
            event="end",
        )
        event = get_event()
        assert event.type == "end"
        assert not event.error
        assert event.error_message is None


@pytest.mark.parametrize("blocking", [False, True])
def test_root_logger(blocking, caplog):
    execinfo = {
        "job_id": None,
        "host_name": None,
        "user_name": None,
        "process_id": None,
        "workflow_id": None,
    }
    with capture_events(blocking) as get_event:
        with caplog.at_level(logging.WARNING):
            events.send_workflow_event(execinfo=execinfo, event="start")
        event = get_event()
        assert event.type == "start"
        assert not caplog.records

        with caplog.at_level(logging.INFO):
            events.send_workflow_event(execinfo=execinfo, event="start")

        event = get_event()
        assert event.type == "start"
        assert len(caplog.records) == 1
        event_root = caplog.records[0]
        assert event_root.type == "start"
