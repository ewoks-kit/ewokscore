import datetime
from contextlib import contextmanager
from logging.handlers import QueueHandler
from queue import Queue, Empty
import pytest
from ewokscore import events
from ewokscore.events import readers
from ewokscore.events import cleanup as cleanup_events


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
        events.remove_handler(handler)
        cleanup_events()


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


def test_sqlite3(tmpdir):
    uri = f"file:{tmpdir / 'ewoks_events.db'}"
    handlers = [
        {
            "class": "ewokscore.events.handlers.Sqlite3EwoksEventHandler",
            "arguments": [{"name": "uri", "value": uri}],
        }
    ]
    assert_event_reader(handlers, readers.Sqlite3EwoksEventReader(uri))


def assert_event_reader(handlers, reader):
    try:
        execinfo = {
            "job_id": 123,
            "workflow_id": 456,
            "host_name": None,
            "user_name": None,
            "process_id": None,
            "handlers": handlers,
        }
        events.send_workflow_event(execinfo=execinfo, event="start")
        events.send_workflow_event(execinfo=execinfo, event="end")

        evts = list(reader.wait_events(timeout=0))
        assert len(evts) == 2

        evts = list(reader.get_events(type="end"))
        assert len(evts) == 1
        evts = list(reader.get_full_job_events(type="end"))
        assert len(evts) == 1
        assert len(evts[0]) == 2
        evts = list(reader.get_events(type="progress"))
        assert len(evts) == 0
        evts = list(reader.get_full_job_events(type="progress"))
        assert len(evts) == 0

        evts = list(reader.get_events(job_id=123))
        assert len(evts) == 2
        evts = list(reader.get_full_job_events(job_id=123))
        assert len(evts) == 1
        assert len(evts[0]) == 2

        now = datetime.datetime.now().astimezone()
        starttime = now - datetime.timedelta(minutes=1)
        endtime = now + datetime.timedelta(minutes=1)
        evts = list(reader.get_events(starttime=starttime, endtime=endtime))
        assert len(evts) == 2
        evts = list(
            reader.get_full_job_events(type="end", starttime=starttime, endtime=endtime)
        )
        assert len(evts) == 1
        assert len(evts[0]) == 2

        evts = list(reader.get_events(endtime=starttime))
        assert len(evts) == 0
        evts = list(reader.get_full_job_events(endtime=starttime))
        assert len(evts) == 0

    finally:
        reader.close()
        cleanup_events()
