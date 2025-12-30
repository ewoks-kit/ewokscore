import logging
import threading
import time
from pprint import pformat
from typing import Dict
from typing import List
from typing import Optional

import pytest
from ewoksutils.event_utils import FIELD_TYPES
from ewoksutils.import_utils import qualname
from ewoksutils.sqlite3_utils import connect
from ewoksutils.sqlite3_utils import select

from ..bindings import execute_graph
from ..events import cleanup as cleanup_events
from ..task import Task

logger = logging.getLogger(__name__)


@pytest.fixture
def sqlite_path(tmp_path):
    try:
        yield tmp_path
    finally:
        cleanup_events()


def test_succesfull_workfow(sqlite_path):
    database = sqlite_path / "ewoks_events.db"
    _run_succesfull_workfow(database, execute_graph)
    events = _fetch_events(database, 10)
    _assert_succesfull_workfow_events(events)


def test_failed_workfow(sqlite_path):
    database = sqlite_path / "ewoks_events.db"
    _run_failed_workfow(database, execute_graph)
    events = _fetch_events(database, 8)
    _assert_failed_workfow_events(events)


def test_changing_handlers(sqlite_path):
    database1 = sqlite_path / "ewoks_events1.db"
    _run_succesfull_workfow(database1, execute_graph)
    events = _fetch_events(database1, 10)
    _assert_sleep_workfow_events(events)

    size_before = database1.stat().st_size

    database2 = sqlite_path / "ewoks_events2.db"
    _run_succesfull_workfow(database2, execute_graph)
    events = _fetch_events(database2, 10)
    _assert_sleep_workfow_events(events)

    size_after = database1.stat().st_size
    assert size_before == size_after


def test_changing_handlers_parallel(sqlite_path, n_concurrent=4):
    databases = [sqlite_path / f"ewoks_events_{i}.db" for i in range(n_concurrent)]

    threads = [
        threading.Thread(target=_run_sleep_workfow, args=(db, execute_graph))
        for db in databases
    ]

    _run_threads(threads)

    sizes = []
    for db in databases:
        events = _fetch_events(db, 10)
        _assert_sleep_workfow_events(events)
        sizes.append(db.stat().st_size)

    assert len(set(sizes)) == 1


def _run_threads(threads):
    for t in threads:
        t.start()

    deadline = time.time() + 20

    for t in threads:
        remaining = deadline - time.time()
        if remaining <= 0:
            pytest.fail("Timeout while waiting for workflow threads to finish")

        t.join(timeout=remaining)

        if t.is_alive():
            pytest.fail(f"Workflow thread {t.name} did not finish within {deadline}s")


class _MyTask(
    Task, input_names=["ctr"], optional_input_names=["error_msg"], output_names=["ctr"]
):
    def run(self):
        if self.inputs.error_msg:
            raise ValueError(self.inputs.error_msg)
        else:
            self.outputs.ctr = self.inputs.ctr + 1


class _MySleepTask(
    Task, input_names=["ctr"], optional_input_names=["error_msg"], output_names=["ctr"]
):

    def run(self):
        time.sleep(0.2)
        self.outputs.ctr = self.inputs.ctr + 1


def _run_succesfull_workfow(database, execute_graph, **execute_options):
    graph = {"id": "test_graph", "schema_version": "1.1"}
    nodes = [
        {
            "id": "node1",
            "task_type": "class",
            "task_identifier": qualname(_MyTask),
            "default_inputs": [{"name": "ctr", "value": 0}],
        },
        {
            "id": "node2",
            "task_type": "class",
            "task_identifier": qualname(_MyTask),
            "default_inputs": [{"name": "ctr", "value": 0}],
        },
        {
            "id": "node3",
            "task_type": "class",
            "task_identifier": qualname(_MyTask),
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
    taskgraph = {"graph": graph, "nodes": nodes, "links": links}
    _execute_graph(database, taskgraph, execute_graph, **execute_options)


def _assert_succesfull_workfow_events(events):
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


def _run_failed_workfow(database, execute_graph, **execute_options):
    graph = {"id": "test_graph", "schema_version": "1.1"}
    nodes = [
        {
            "id": "node1",
            "task_type": "class",
            "task_identifier": qualname(_MyTask),
            "default_inputs": [{"name": "ctr", "value": 0}],
        },
        {
            "id": "node2",
            "task_type": "class",
            "task_identifier": qualname(_MyTask),
            "default_inputs": [
                {"name": "ctr", "value": 0},
                {"name": "error_msg", "value": "abc"},
            ],
        },
        {
            "id": "node3",
            "task_type": "class",
            "task_identifier": qualname(_MyTask),
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
    graph = {"graph": graph, "nodes": nodes, "links": links}
    _execute_graph(database, graph, execute_graph, **execute_options)


def _assert_failed_workfow_events(events):
    err_msg = "Execution failed for ewoks task 'node2' (id: 'node2', task: 'ewokscore.tests.test_workflow_events._MyTask'): abc"

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
        {
            "context": "node",
            "node_id": "node2",
            "type": "end",
            "error_message": "abc",
        },
        {
            "context": "workflow",
            "node_id": None,
            "type": "end",
            "error_message": err_msg,
        },
        {
            "context": "job",
            "node_id": None,
            "type": "end",
            "error_message": err_msg,
        },
    ]
    captured = [
        {k: event[k] for k in ("context", "node_id", "type", "error_message")}
        for event in events
    ]
    _assert_events(expected, captured)


def _run_sleep_workfow(database, execute_graph, **execute_options):
    graph = {"id": "test_graph", "schema_version": "1.1"}
    nodes = [
        {
            "id": "node1",
            "task_type": "class",
            "task_identifier": qualname(_MySleepTask),
            "default_inputs": [{"name": "ctr", "value": 0}],
        },
        {
            "id": "node2",
            "task_type": "class",
            "task_identifier": qualname(_MySleepTask),
            "default_inputs": [{"name": "ctr", "value": 0}],
        },
        {
            "id": "node3",
            "task_type": "class",
            "task_identifier": qualname(_MySleepTask),
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
    taskgraph = {"graph": graph, "nodes": nodes, "links": links}
    _execute_graph(database, taskgraph, execute_graph, **execute_options)


def _assert_sleep_workfow_events(events):
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


def _execute_graph(database, graph, execute_graph, **execute_options):
    execinfo = execute_options.setdefault("execinfo", dict())
    handlers = execinfo.setdefault("handlers", list())
    handlers.append(
        {
            "class": "ewokscore.events.handlers.Sqlite3EwoksEventHandler",
            "arguments": [{"name": "uri", "value": database}],
        }
    )
    try:
        execute_graph(graph, **execute_options)
    except RuntimeError:
        pass


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


def _fetch_events(database: str, nevents: int) -> List[Dict[str, Optional[str]]]:
    """Events are handled asynchronously so wait until we have the required `nevents`
    up to 3 seconds.
    """
    exception = None
    events = list()
    for _ in range(30):
        try:
            with connect(database) as conn:
                events = list(select(conn, "ewoks_events", field_types=FIELD_TYPES))

            if len(events) != nevents:
                raise RuntimeError(f"{len(events)} ewoks events instead of {nevents}")
            return events
        except Exception as e:
            exception = e
            time.sleep(0.1)
    if exception:
        logger.error(exception)
    return events
