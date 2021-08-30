import json
import pytest
from ewokscore import load_graph


def savegraph(graph, tmpdir, name):
    filename = name + ".json"
    with open(tmpdir / filename, mode="w") as f:
        json.dump(graph, f, indent=2)
    return filename


@pytest.fixture
def subsubsubgraph(tmpdir):
    graph = {
        "nodes": [
            {
                "id": "task1",
                "task_type": "method",
                "task_identifier": "ewokscore.tests.examples.tasks.simplemethods.add",
            },
            {
                "id": "task2",
                "task_type": "method",
                "task_identifier": "ewokscore.tests.examples.tasks.simplemethods.add",
            },
        ],
        "links": [
            {"source": "task1", "target": "task2", "arguments": {0: "return_value"}},
        ],
    }

    return savegraph(graph, tmpdir, "subsubsubgraph")


@pytest.fixture
def subsubgraph(tmpdir, subsubsubgraph):
    graph = {
        "nodes": [
            {
                "id": "task1",
                "task_type": "method",
                "task_identifier": "ewokscore.tests.examples.tasks.simplemethods.add",
            },
            {
                "id": "task2",
                "task_type": "method",
                "task_identifier": "ewokscore.tests.examples.tasks.simplemethods.add",
            },
            {
                "id": "subsubsubgraph",
                "task_type": "graph",
                "task_identifier": subsubsubgraph,
            },
        ],
        "links": [
            {"source": "task1", "target": "task2", "arguments": {0: "return_value"}},
            {
                "source": "task2",
                "target": "subsubsubgraph",
                "arguments": {0: "return_value"},
                "sub_graph_nodes": {"sub_target": "task1"},
            },
        ],
    }
    return savegraph(graph, tmpdir, "subsubgraph")


@pytest.fixture
def subgraph(tmpdir, subsubgraph):
    graph = {
        "nodes": [
            {
                "id": "task1",
                "task_type": "method",
                "task_identifier": "ewokscore.tests.examples.tasks.simplemethods.add",
            },
            {
                "id": "task2",
                "task_type": "method",
                "task_identifier": "ewokscore.tests.examples.tasks.simplemethods.add",
            },
            {"id": "subsubgraph", "task_type": "graph", "task_identifier": subsubgraph},
        ],
        "links": [
            {"source": "task1", "target": "task2", "arguments": {0: "return_value"}},
            {
                "source": "task2",
                "target": "subsubgraph",
                "arguments": {0: "return_value"},
                "sub_graph_nodes": {"sub_target": "task1"},
            },
        ],
    }
    return savegraph(graph, tmpdir, "subgraph")


@pytest.fixture
def graph(tmpdir, subgraph):
    graph = {
        "nodes": [
            {"id": "subgraph1", "task_type": "graph", "task_identifier": subgraph},
            {"id": "subgraph2", "task_type": "graph", "task_identifier": subgraph},
            {
                "id": "append",
                "task_type": "method",
                "task_identifier": "ewokscore.tests.examples.tasks.simplemethods.append",
            },
        ],
        "links": [
            {
                "source": "subgraph1",
                "target": "subgraph2",
                "arguments": {0: "return_value"},
                "sub_graph_nodes": {
                    "sub_source": "subsubgraph",
                    "sub_target": "task1",
                    "sub_graph_nodes": {
                        "sub_source": "subsubsubgraph",
                        "sub_graph_nodes": {"sub_source": "task2"},
                    },
                },
            },
            # Expanded sub-links
            {
                "source": "subgraph1",
                "target": "append",
                "arguments": {0: "return_value"},
                "sub_graph_nodes": {"sub_source": "task1"},
            },
            {
                "source": "subgraph1",
                "target": "append",
                "arguments": {1: "return_value"},
                "sub_graph_nodes": {"sub_source": "task2"},
            },
            {
                "source": "subgraph1",
                "target": "append",
                "arguments": {2: "return_value"},
                "sub_graph_nodes": {
                    "sub_source": "subsubgraph",
                    "sub_graph_nodes": {"sub_source": "task1"},
                },
            },
            {
                "source": "subgraph1",
                "target": "append",
                "arguments": {3: "return_value"},
                "sub_graph_nodes": {
                    "sub_source": "subsubgraph",
                    "sub_graph_nodes": {"sub_source": "task2"},
                },
            },
            {
                "source": "subgraph1",
                "target": "append",
                "arguments": {4: "return_value"},
                "sub_graph_nodes": {
                    "sub_source": "subsubgraph",
                    "sub_graph_nodes": {
                        "sub_source": "subsubsubgraph",
                        "sub_graph_nodes": {"sub_source": "task1"},
                    },
                },
            },
            {
                "source": "subgraph1",
                "target": "append",
                "arguments": {5: "return_value"},
                "sub_graph_nodes": {
                    "sub_source": "subsubgraph",
                    "sub_graph_nodes": {
                        "sub_source": "subsubsubgraph",
                        "sub_graph_nodes": {"sub_source": "task2"},
                    },
                },
            },
            # Flat sub-links (1 level deep because the source and target need to be a valid node id)
            {
                "source": "subgraph2",
                "target": "append",
                "arguments": {6: "return_value"},
                "sub_graph_nodes": {"sub_source": "task1"},
            },
            {
                "source": "subgraph2",
                "target": "append",
                "arguments": {7: "return_value"},
                "sub_graph_nodes": {"sub_source": "task2"},
            },
            {
                "source": "subgraph2",
                "target": "append",
                "arguments": {8: "return_value"},
                "sub_graph_nodes": {
                    "sub_source": ("subsubgraph", "task1"),
                },
            },
            {
                "source": "subgraph2",
                "target": "append",
                "arguments": {9: "return_value"},
                "sub_graph_nodes": {"sub_source": ("subsubgraph", "task2")},
            },
            {
                "source": "subgraph2",
                "target": "append",
                "arguments": {10: "return_value"},
                "sub_graph_nodes": {
                    "sub_source": ("subsubgraph", ("subsubsubgraph", "task1"))
                },
            },
            {
                "source": "subgraph2",
                "target": "append",
                "arguments": {11: "return_value"},
                "sub_graph_nodes": {
                    "sub_source": ("subsubgraph", ("subsubsubgraph", "task2"))
                },
            },
        ],
    }
    return savegraph(graph, tmpdir, "graph")


def test_load_from_json(tmpdir, graph):
    taskgraph = load_graph(graph, root_dir=str(tmpdir))
    tasks = taskgraph.execute()

    assert len(tasks) == 13

    task = tasks[("subgraph1", "task1")]
    assert task.outputs.return_value == 1
    task = tasks[("subgraph1", "task2")]
    assert task.outputs.return_value == 2
    task = tasks[("subgraph1", ("subsubgraph", "task1"))]
    assert task.outputs.return_value == 3
    task = tasks[("subgraph1", ("subsubgraph", "task2"))]
    assert task.outputs.return_value == 4
    task = tasks[("subgraph1", ("subsubgraph", ("subsubsubgraph", "task1")))]
    assert task.outputs.return_value == 5
    task = tasks[("subgraph1", ("subsubgraph", ("subsubsubgraph", "task2")))]
    assert task.outputs.return_value == 6

    task = tasks[("subgraph2", "task1")]
    assert task.outputs.return_value == 7
    task = tasks[("subgraph2", "task2")]
    assert task.outputs.return_value == 8
    task = tasks[("subgraph2", ("subsubgraph", "task1"))]
    assert task.outputs.return_value == 9
    task = tasks[("subgraph2", ("subsubgraph", "task2"))]
    assert task.outputs.return_value == 10
    task = tasks[("subgraph2", ("subsubgraph", ("subsubsubgraph", "task1")))]
    assert task.outputs.return_value == 11
    task = tasks[("subgraph2", ("subsubgraph", ("subsubsubgraph", "task2")))]
    assert task.outputs.return_value == 12

    task = tasks["append"]
    assert task.outputs.return_value == tuple(range(1, 13))
