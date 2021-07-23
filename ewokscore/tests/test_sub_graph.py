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
                "method": "ewokscore.tests.examples.tasks.simplemethods.add",
            },
            {
                "id": "task2",
                "method": "ewokscore.tests.examples.tasks.simplemethods.add",
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
                "method": "ewokscore.tests.examples.tasks.simplemethods.add",
            },
            {
                "id": "task2",
                "method": "ewokscore.tests.examples.tasks.simplemethods.add",
            },
            {"id": "subsubsubgraph", "graph": subsubsubgraph},
        ],
        "links": [
            {"source": "task1", "target": "task2", "arguments": {0: "return_value"}},
            {
                "source": "task2",
                "target": "subsubsubgraph",
                "links": [{"target": "task1", "arguments": {0: "return_value"}}],
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
                "method": "ewokscore.tests.examples.tasks.simplemethods.add",
            },
            {
                "id": "task2",
                "method": "ewokscore.tests.examples.tasks.simplemethods.add",
            },
            {"id": "subsubgraph", "graph": subsubgraph},
        ],
        "links": [
            {"source": "task1", "target": "task2", "arguments": {0: "return_value"}},
            {
                "source": "task2",
                "target": "subsubgraph",
                "links": [{"target": "task1", "arguments": {0: "return_value"}}],
            },
        ],
    }
    return savegraph(graph, tmpdir, "subgraph")


@pytest.fixture
def graph(tmpdir, subgraph):
    graph = {
        "nodes": [
            {"id": "subgraph1", "graph": subgraph},
            {"id": "subgraph2", "graph": subgraph},
            {
                "id": "append",
                "method": "ewokscore.tests.examples.tasks.simplemethods.append",
            },
        ],
        "links": [
            {
                "source": "subgraph1",
                "target": "subgraph2",
                "links": [
                    {
                        "source": "subsubgraph",
                        "target": "task1",
                        "links": [
                            {
                                "source": "subsubsubgraph",
                                "links": [
                                    {
                                        "source": "task2",
                                        "arguments": {0: "return_value"},
                                    }
                                ],
                            },
                        ],
                    },
                ],
            },
            # Expanded sub-links
            {
                "source": "subgraph1",
                "target": "append",
                "links": [
                    {"source": "task1", "arguments": {0: "return_value"}},
                    {"source": "task2", "arguments": {1: "return_value"}},
                    {
                        "source": "subsubgraph",
                        "links": [
                            {"source": "task1", "arguments": {2: "return_value"}},
                            {"source": "task2", "arguments": {3: "return_value"}},
                            {
                                "source": "subsubsubgraph",
                                "links": [
                                    {
                                        "source": "task1",
                                        "arguments": {4: "return_value"},
                                    },
                                    {
                                        "source": "task2",
                                        "arguments": {5: "return_value"},
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            # Flat sub-links (1 level deep because the source and target need to be a valid node id)
            {
                "source": "subgraph2",
                "target": "append",
                "links": [
                    {"source": "task1", "arguments": {6: "return_value"}},
                    {"source": "task2", "arguments": {7: "return_value"}},
                    {
                        "source": ("subsubgraph", "task1"),
                        "arguments": {8: "return_value"},
                    },
                    {
                        "source": ("subsubgraph", "task2"),
                        "arguments": {9: "return_value"},
                    },
                    {
                        "source": ("subsubgraph", ("subsubsubgraph", "task1")),
                        "arguments": {10: "return_value"},
                    },
                    {
                        "source": ("subsubgraph", ("subsubsubgraph", "task2")),
                        "arguments": {11: "return_value"},
                    },
                ],
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
