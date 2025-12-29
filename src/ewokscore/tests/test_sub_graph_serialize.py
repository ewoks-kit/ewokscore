import json

import pytest
import yaml

from ..bindings import execute_graph
from ..graph import load_graph


def subsubsubgraph():
    return {
        "graph": {
            "id": "subsubsubgraph",
            "schema_version": "1.1",
            "input_nodes": [{"id": "in", "node": "task1"}, {"id": "notconnected"}],
            "output_nodes": [{"id": "out", "node": "task2"}, {"id": "notconnected"}],
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
                "data_mapping": [{"source_output": "return_value", "target_input": 0}],
            },
        ],
    }


def subsubgraph(_subsubsubgraph):
    return {
        "graph": {
            "id": "subsubgraph",
            "schema_version": "1.1",
            "input_nodes": [{"id": "in", "node": "task1"}, {"id": "notconnected"}],
            "output_nodes": [
                {"id": "out", "node": "subsubsubgraph", "sub_node": "out"},
                {"id": "notconnected"},
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
                "task_identifier": _subsubsubgraph,
            },
        ],
        "links": [
            {
                "source": "task1",
                "target": "task2",
                "data_mapping": [{"source_output": "return_value", "target_input": 0}],
            },
            {
                "source": "task2",
                "target": "subsubsubgraph",
                "sub_target": "in",
                "data_mapping": [{"source_output": "return_value", "target_input": 0}],
            },
        ],
    }


def subgraph(_subsubgraph):
    return {
        "graph": {
            "id": "subgraph",
            "schema_version": "1.1",
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
            {
                "id": "subsubgraph",
                "task_type": "graph",
                "task_identifier": _subsubgraph,
            },
        ],
        "links": [
            {
                "source": "task1",
                "target": "task2",
                "data_mapping": [{"source_output": "return_value", "target_input": 0}],
            },
            {
                "source": "task2",
                "target": "subsubgraph",
                "sub_target": "in",
                "data_mapping": [{"source_output": "return_value", "target_input": 0}],
            },
        ],
    }


def graph(_subgraph):
    return {
        "graph": {"id": "graph", "schema_version": "1.1"},
        "nodes": [
            {"id": "subgraph1", "task_type": "graph", "task_identifier": _subgraph},
            {"id": "subgraph2", "task_type": "graph", "task_identifier": _subgraph},
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
                "data_mapping": [{"source_output": "return_value", "target_input": 0}],
            },
            # Link all nodes from "subgraph1" to "append"
            {
                "source": "subgraph1",
                "sub_source": "task1",
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 0}],
            },
            {
                "source": "subgraph1",
                "sub_source": "task2",
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 1}],
            },
            {
                "source": "subgraph1",
                "sub_source": ("subsubgraph", "task1"),
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 2}],
            },
            {
                "source": "subgraph1",
                "sub_source": ("subsubgraph", "task2"),
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 3}],
            },
            {
                "source": "subgraph1",
                "sub_source": ("subsubgraph", ("subsubsubgraph", "task1")),
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 4}],
            },
            {
                "source": "subgraph1",
                "sub_source": ("subsubgraph", ("subsubsubgraph", "task2")),
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 5}],
            },
            # Link all nodes from "subgraph2" to "append"
            {
                "source": "subgraph2",
                "sub_source": "task1",
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 6}],
            },
            {
                "source": "subgraph2",
                "sub_source": "task2",
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 7}],
            },
            {
                "source": "subgraph2",
                "sub_source": ("subsubgraph", "task1"),
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 8}],
            },
            {
                "source": "subgraph2",
                "sub_source": ("subsubgraph", "task2"),
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 9}],
            },
            {
                "source": "subgraph2",
                "sub_source": ("subsubgraph", ("subsubsubgraph", "task1")),
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 10}],
            },
            {
                "source": "subgraph2",
                "sub_source": ("subsubgraph", ("subsubsubgraph", "task2")),
                "target": "append",
                "data_mapping": [{"source_output": "return_value", "target_input": 11}],
            },
        ],
    }


def savegraph(graph, tmp_path, name, representation="json"):
    if representation == "json":
        filename = name + ".json"
        with open(tmp_path / filename, mode="w") as f:
            json.dump(graph, f, indent=2)
    elif representation == "yaml":
        filename = name + ".yml"
        with open(tmp_path / filename, mode="w") as f:
            yaml.dump(graph, f)
    else:
        raise ValueError(representation)
    return filename


def serialized_graph(tmp_path, representation="json") -> str:
    subname = savegraph(
        subsubsubgraph(), tmp_path, "subsubsubgraph", representation=representation
    )
    subname = savegraph(
        subsubgraph(subname), tmp_path, "subsubgraph", representation=representation
    )
    subname = savegraph(
        subgraph(subname), tmp_path, "subgraph", representation=representation
    )
    return savegraph(graph(subname), tmp_path, "graph", representation=representation)


def nonserialized_graph() -> dict:
    return graph(subgraph(subsubgraph(subsubsubgraph())))


@pytest.mark.parametrize(
    "representation", (None, "json", "json_dict", "json_string", "yaml")
)
def test_sub_graph_serialize(representation, tmp_path):
    ewoksgraph = load_graph(nonserialized_graph())
    if representation == "yaml":
        destination = str(tmp_path / "file.yml")
    elif representation == "json":
        destination = str(tmp_path / "file.json")
    else:
        destination = None
    inmemorydump = ewoksgraph.dump(destination, representation=representation)

    if destination:
        source = destination
    else:
        source = inmemorydump
    ewoksgraph2 = load_graph(source, representation=representation)

    assert ewoksgraph == ewoksgraph2


@pytest.mark.parametrize("representation", ("json", "yaml"))
def test_sub_graph_execute(representation, tmp_path):
    g = serialized_graph(tmp_path, representation=representation)
    ewoksgraph = load_graph(g, root_dir=str(tmp_path))

    tasks = execute_graph(ewoksgraph, output_tasks=True)

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
