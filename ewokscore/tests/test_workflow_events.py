import logging
from pprint import pformat
import sqlite3
from time import sleep
from typing import Dict, List, Optional

from ewoksutils.import_utils import qualname
from ewoksutils.sqlite3_utils import select
from ewoksutils.event_utils import FIELD_TYPES

from ewokscore import execute_graph
from ewokscore import Task
from ewokscore.events import cleanup as cleanup_events


logger = logging.getLogger(__name__)


def test_succesfull_workfow(tmpdir):
    uri = run_succesfull_workfow(tmpdir, execute_graph)
    events = fetch_events(uri, 10)
    assert_succesfull_workfow_events(events)


def test_failed_workfow(tmpdir):
    uri = run_failed_workfow(tmpdir, execute_graph)
    events = fetch_events(uri, 8)
    assert_failed_workfow_events(events)


class MyTask(
    Task, input_names=["ctr"], optional_input_names=["error_msg"], output_names=["ctr"]
):
    def run(self):
        if self.inputs.error_msg:
            raise ValueError(self.inputs.error_msg)
        else:
            self.outputs.ctr = self.inputs.ctr + 1


def run_succesfull_workfow(tmpdir, execute_graph, **execute_options):
    nodes = [
        {
            "id": "node1",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [{"name": "ctr", "value": 0}],
        },
        {
            "id": "node2",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [{"name": "ctr", "value": 0}],
        },
        {
            "id": "node3",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [{"name": "ctr", "value": 0}],
        },
    ]
    links = [
        {
            "source": "node1",
            "target": "node2",
            "data_mapping": [{"source_output": "ctr", "target_input": "ctr"}],
        },
        {
            "source": "node2",
            "target": "node3",
            "data_mapping": [{"source_output": "ctr", "target_input": "ctr"}],
        },
    ]
    graph = {"graph": {"id": "test_graph"}, "nodes": nodes, "links": links}
    return _execute_graph(tmpdir, graph, execute_graph, **execute_options)


def assert_succesfull_workfow_events(events):
    expected = [
        {"context": "job", "node_id": None, "type": "start"},
        {"context": "workflow", "node_id": None, "type": "start"},
        {"context": "node", "node_id": "node1", "type": "start"},
        {"context": "node", "node_id": "node1", "type": "end"},
        {"context": "node", "node_id": "node2", "type": "start"},
        {"context": "node", "node_id": "node2", "type": "end"},
        {"context": "node", "node_id": "node3", "type": "start"},
        {"context": "node", "node_id": "node3", "type": "end"},
        {"context": "workflow", "node_id": None, "type": "end"},
        {"context": "job", "node_id": None, "type": "end"},
    ]
    captured = [
        {k: event[k] for k in ("context", "node_id", "type")} for event in events
    ]
    _assert_events(expected, captured)


def run_failed_workfow(tmpdir, execute_graph, **execute_options):
    nodes = [
        {
            "id": "node1",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [{"name": "ctr", "value": 0}],
        },
        {
            "id": "node2",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [
                {"name": "ctr", "value": 0},
                {"name": "error_msg", "value": "abc"},
            ],
        },
        {
            "id": "node3",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [{"name": "ctr", "value": 0}],
        },
    ]
    links = [
        {
            "source": "node1",
            "target": "node2",
            "data_mapping": [{"source_output": "ctr", "target_input": "ctr"}],
        },
        {
            "source": "node2",
            "target": "node3",
            "data_mapping": [{"source_output": "ctr", "target_input": "ctr"}],
        },
    ]
    graph = {"graph": {"id": "test_graph"}, "nodes": nodes, "links": links}
    return _execute_graph(tmpdir, graph, execute_graph, **execute_options)


def assert_failed_workfow_events(events):
    expected = [
        {
            "context": "job",
            "node_id": None,
            "type": "start",
            "error_message": None,
        },
        {
            "context": "workflow",
            "node_id": None,
            "type": "start",
            "error_message": None,
        },
        {
            "context": "node",
            "node_id": "node1",
            "type": "start",
            "error_message": None,
        },
        {
            "context": "node",
            "node_id": "node1",
            "type": "end",
            "error_message": None,
        },
        {
            "context": "node",
            "node_id": "node2",
            "type": "start",
            "error_message": None,
        },
        {"context": "node", "node_id": "node2", "type": "end", "error_message": "abc"},
        {
            "context": "workflow",
            "node_id": None,
            "type": "end",
            "error_message": "Task 'node2' failed",
        },
        {
            "context": "job",
            "node_id": None,
            "type": "end",
            "error_message": "Task 'node2' failed",
        },
    ]
    captured = [
        {k: event[k] for k in ("context", "node_id", "type", "error_message")}
        for event in events
    ]
    _assert_events(expected, captured)


def _execute_graph(tmpdir, graph, execute_graph, **execute_options):
    uri = f"file:{tmpdir / 'ewoks_events.db'}"
    execinfo = execute_options.setdefault("execinfo", dict())
    handlers = execinfo.setdefault("handlers", list())
    handlers.append(
        {
            "class": "ewokscore.events.handlers.Sqlite3EwoksEventHandler",
            "arguments": [{"name": "uri", "value": uri}],
        }
    )
    cleanup_events()
    try:
        execute_graph(graph, **execute_options)
    except RuntimeError:
        pass
    return uri


def _assert_events(expected, captured):
    missing = list()
    unexpected = list(captured)
    for event in expected:
        try:
            unexpected.remove(event)
        except ValueError:
            missing.append(event)
    if missing or unexpected:
        raise AssertionError(
            f"ewoks events not as expected\nmissing:\n{pformat(missing)}\nunexpected:\n{unexpected}"
        )


def fetch_events(uri: str, nevents: int) -> List[Dict[str, Optional[str]]]:
    """Events are handled asynchronously so wait until we have the required `nevents`
    up to 3 seconds.
    """
    try:
        exception = None
        events = list()
        for _ in range(30):
            try:
                with sqlite3.connect(uri, uri=True) as conn:
                    events = list(select(conn, "ewoks_events", field_types=FIELD_TYPES))

                if len(events) != nevents:
                    raise RuntimeError(
                        f"{len(events)} ewoks events instead of {nevents}"
                    )
                return events
            except Exception as e:
                exception = e
                sleep(0.1)
        if exception:
            logger.error(exception)
        return events
    finally:
        cleanup_events()
