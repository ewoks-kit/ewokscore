import logging
import threading
import time
from pathlib import Path
from pprint import pformat
from typing import Dict
from typing import Generator
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
def sqlite_path(tmp_path) -> Generator[Path, None, None]:
    try:
        yield tmp_path
    finally:
        cleanup_events()


def test_succesfull_workfow(sqlite_path: Path):
    database = sqlite_path / "ewoks_events.db"
    run_succesfull_workfow(database, execute_graph)
    events = fetch_events(database, 10)
    assert_succesfull_workfow_events(events)


def test_failed_workfow(sqlite_path: Path):
    database = sqlite_path / "ewoks_events.db"
    run_failed_workfow(database, execute_graph)
    events = fetch_events(database, 8)
    assert_failed_workfow_events(events)


def test_changing_handlers(sqlite_path: Path):
    database1 = sqlite_path / "ewoks_events1.db"
    run_succesfull_workfow(database1, execute_graph, delay=0.2)
    events = fetch_events(database1, 10)
    assert_succesfull_workfow_events(events)

    size_before = database1.stat().st_size

    database2 = sqlite_path / "ewoks_events2.db"
    run_succesfull_workfow(database2, execute_graph, delay=0.2)
    events = fetch_events(database2, 10)
    assert_succesfull_workfow_events(events)

    size_after = database1.stat().st_size
    assert size_before == size_after


def test_changing_handlers_parallel(sqlite_path: Path, n_concurrent: int = 4):
    databases = [sqlite_path / f"ewoks_events_{i}.db" for i in range(n_concurrent)]

    threads = [
        threading.Thread(
            target=run_succesfull_workfow,
            args=(db, execute_graph),
            kwargs=dict(delay=0.2),
        )
        for db in databases
    ]

    _run_threads(threads)

    sizes = []
    for db in databases:
        events = fetch_events(db, 10)
        assert_succesfull_workfow_events(events)
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


class MyTask(
    Task,
    input_names=["ctr"],
    optional_input_names=["error_msg", "delay"],
    output_names=["ctr"],
):
    def run(self):
        if self.inputs.error_msg:
            raise ValueError(self.inputs.error_msg)
        else:
            self.outputs.ctr = self.inputs.ctr + 1
        if self.inputs.delay:
            time.sleep(self.inputs.delay)


def run_succesfull_workfow(
    database: Path, execute_graph, delay: int = 0, **execute_options
):
    graph = {"id": "test_graph", "schema_version": "1.1"}
    nodes = [
        {
            "id": "node1",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [
                {"name": "ctr", "value": 0},
                {"name": "delay", "value": delay},
            ],
        },
        {
            "id": "node2",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [
                {"name": "ctr", "value": 0},
                {"name": "delay", "value": delay},
            ],
        },
        {
            "id": "node3",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [
                {"name": "ctr", "value": 0},
                {"name": "delay", "value": delay},
            ],
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


def run_failed_workfow(
    database, execute_graph, delay: int = 0, **execute_options
) -> None:
    graph = {"id": "test_graph", "schema_version": "1.1"}
    nodes = [
        {
            "id": "node1",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [
                {"name": "ctr", "value": 0},
                {"name": "delay", "value": delay},
            ],
        },
        {
            "id": "node2",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [
                {"name": "ctr", "value": 0},
                {"name": "error_msg", "value": "abc"},
                {"name": "delay", "value": delay},
            ],
        },
        {
            "id": "node3",
            "task_type": "class",
            "task_identifier": qualname(MyTask),
            "default_inputs": [
                {"name": "ctr", "value": 0},
                {"name": "delay", "value": delay},
            ],
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


def assert_failed_workfow_events(events):
    err_msg = "Execution failed for ewoks task 'node2' (id: 'node2', task: 'ewokscore.tests.test_workflow_events.MyTask'): abc"

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


def _execute_graph(database, graph, execute_graph, **execute_options) -> None:
    execinfo = execute_options.setdefault("execinfo", dict())
    handlers = execinfo.setdefault("handlers", list())
    handlers.append(
        {
            "class": "ewokscore.events.handlers.Sqlite3EwoksEventHandler",
            "arguments": [{"name": "uri", "value": str(database)}],
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


def fetch_events(database: Path, nevents: int) -> List[Dict[str, Optional[str]]]:
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
