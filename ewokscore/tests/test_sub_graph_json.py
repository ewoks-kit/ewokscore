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
        "graph": {
            "input_nodes": [{"id": "in", "node": "task1"}],
            "output_nodes": [{"id": "out", "node": "task2"}],
        },
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
            {
                "source": "task1",
                "target": "task2",
                "data_mapping": [{"target_input": 0, "source_output": "return_value"}],
            },
        ],
    }

    return savegraph(graph, tmpdir, "subsubsubgraph")


@pytest.fixture
def subsubgraph(tmpdir, subsubsubgraph):
    graph = {
        "graph": {
            "input_nodes": [{"id": "in", "node": "task1"}],
            "output_nodes": [
                {"id": "out", "node": "subsubsubgraph", "sub_node": "out"}
            ],
        },
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
            {
                "source": "task1",
                "target": "task2",
                "data_mapping": [{"target_input": 0, "source_output": "return_value"}],
            },
            {
                "source": "task2",
                "target": "subsubsubgraph",
                "sub_target": "in",
                "data_mapping": [{"target_input": 0, "source_output": "return_value"}],
            },
        ],
    }
    return savegraph(graph, tmpdir, "subsubgraph")


@pytest.fixture
def subgraph(tmpdir, subsubgraph):
    graph = {
        "graph": {
            "input_nodes": [{"id": "in", "node": "task1"}],
            "output_nodes": [{"id": "out", "node": "subsubgraph", "sub_node": "out"}],
        },
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
            {
                "source": "task1",
                "target": "task2",
                "data_mapping": [{"target_input": 0, "source_output": "return_value"}],
            },
            {
                "source": "task2",
                "target": "subsubgraph",
                "sub_target": "in",
                "data_mapping": [{"target_input": 0, "source_output": "return_value"}],
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
                "sub_source": "out",
                "target": "subgraph2",
                "sub_target": "in",
                "data_mapping": [{"target_input": 0, "source_output": "return_value"}],
            },
            # Link all nodes from "subgraph1" to "append"
            {
                "source": "subgraph1",
                "sub_source": "task1",
                "target": "append",
                "data_mapping": [{"target_input": 0, "source_output": "return_value"}],
            },
            {
                "source": "subgraph1",
                "sub_source": "task2",
                "target": "append",
                "data_mapping": [{"target_input": 1, "source_output": "return_value"}],
            },
            {
                "source": "subgraph1",
                "sub_source": ("subsubgraph", "task1"),
                "target": "append",
                "data_mapping": [{"target_input": 2, "source_output": "return_value"}],
            },
            {
                "source": "subgraph1",
                "sub_source": ("subsubgraph", "task2"),
                "target": "append",
                "data_mapping": [{"target_input": 3, "source_output": "return_value"}],
            },
            {
                "source": "subgraph1",
                "sub_source": ("subsubgraph", ("subsubsubgraph", "task1")),
                "target": "append",
                "data_mapping": [{"target_input": 4, "source_output": "return_value"}],
            },
            {
                "source": "subgraph1",
                "sub_source": ("subsubgraph", ("subsubsubgraph", "task2")),
                "target": "append",
                "data_mapping": [{"target_input": 5, "source_output": "return_value"}],
            },
            # Link all nodes from "subgraph2" to "append"
            {
                "source": "subgraph2",
                "sub_source": "task1",
                "target": "append",
                "data_mapping": [{"target_input": 6, "source_output": "return_value"}],
            },
            {
                "source": "subgraph2",
                "sub_source": "task2",
                "target": "append",
                "data_mapping": [{"target_input": 7, "source_output": "return_value"}],
            },
            {
                "source": "subgraph2",
                "sub_source": ("subsubgraph", "task1"),
                "target": "append",
                "data_mapping": [{"target_input": 8, "source_output": "return_value"}],
            },
            {
                "source": "subgraph2",
                "sub_source": ("subsubgraph", "task2"),
                "target": "append",
                "data_mapping": [{"target_input": 9, "source_output": "return_value"}],
            },
            {
                "source": "subgraph2",
                "sub_source": ("subsubgraph", ("subsubsubgraph", "task1")),
                "target": "append",
                "data_mapping": [{"target_input": 10, "source_output": "return_value"}],
            },
            {
                "source": "subgraph2",
                "sub_source": ("subsubgraph", ("subsubsubgraph", "task2")),
                "target": "append",
                "data_mapping": [{"target_input": 11, "source_output": "return_value"}],
            },
        ],
    }
    return savegraph(graph, tmpdir, "graph")


def test_load_from_json(tmpdir, graph):
    taskgraph = load_graph(graph, root_dir=str(tmpdir))
    tasks = taskgraph.execute(results_of_all_nodes=True)

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
