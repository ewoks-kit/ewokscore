import logging
import threading
from contextlib import contextmanager
from logging.handlers import QueueHandler
from queue import Empty
from queue import Queue

import pytest
from ewoksutils import sqlite3_utils
from ewoksutils.event_utils import FIELD_TYPES

from .. import events
from ..events import global_state


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


def test_workflow_event_error_log_level(caplog):
    execinfo = {
        "job_id": None,
        "host_name": None,
        "user_name": None,
        "process_id": None,
        "workflow_id": None,
    }
    with capture_events(blocking=True) as get_event:
        with caplog.at_level(logging.DEBUG):
            events.send_workflow_event(
                execinfo=execinfo,
                event="end",
                exception=RuntimeError("something failed"),
            )
        get_event()
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.ERROR


def test_concurrent_send(tmp_path):
    """Sending events concurrently is thread-safe, including the first
    event which instantiates and registers the event handlers."""
    uri = f"file:{tmp_path / 'ewoks_events.db'}"
    handlers = [
        {
            "class": "ewokscore.events.handlers.Sqlite3EwoksEventHandler",
            "arguments": [{"name": "uri", "value": uri}],
        }
    ]

    nthreads = 8
    nevents_per_thread = 10
    barrier = threading.Barrier(nthreads, timeout=10)
    exceptions = list()

    def send_events(job_id):
        execinfo = {
            "job_id": job_id,
            "host_name": None,
            "user_name": None,
            "process_id": None,
            "workflow_id": None,
            "handlers": handlers,
        }
        try:
            # Send the first event from all threads at the same time
            barrier.wait()
            for _ in range(nevents_per_thread // 2):
                events.send_workflow_event(execinfo=execinfo, event="start")
                events.send_workflow_event(execinfo=execinfo, event="end")
        except BaseException as ex:
            exceptions.append(ex)

    threads = [
        threading.Thread(target=send_events, args=(str(job_id),))
        for job_id in range(nthreads)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    try:
        assert not exceptions
        logger = logging.getLogger(global_state.EWOKS_EVENT_LOGGER_NAME)
        assert len(logger.handlers) == 1
    finally:
        events.cleanup()

    with sqlite3_utils.connect(uri, uri=True) as conn:
        rows = list(
            sqlite3_utils.select(conn, "ewoks_events", field_types=FIELD_TYPES)
        )
    assert len(rows) == nthreads * nevents_per_thread
