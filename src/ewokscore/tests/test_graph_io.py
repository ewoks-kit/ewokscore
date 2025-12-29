import pytest

from ..bindings import load_graph
from ..graph import graph_io


@pytest.fixture(scope="module")
def graph():
    graph = {"id": "testgraph", "schema_version": "1.1"}
    nodes = [
        {
            "id": "task1",
            "label": "a",
            "default_inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": "mypackage.mymodule.Task1",
        },
        {
            "id": "task2",
            "label": "a",
            "default_inputs": [{"name": "a", "value": 2}],
            "task_type": "class",
            "task_identifier": "mypackage.mymodule.Task2",
        },
        {
            "id": "task3",
            "label": "b",
            "default_inputs": [{"name": "a", "value": 3}],
            "task_type": "class",
            "task_identifier": "mypackage.mymodule.Task1",
        },
        {
            "id": "task4",
            "label": "c",
            "default_inputs": [{"name": "a", "value": 4}],
            "task_type": "class",
            "task_identifier": "mypackage.mymodule.Task2",
        },
    ]

    links = [
        {
            "source": "task1",
            "target": "task2",
        },
        {
            "source": "task2",
            "target": "task3",
        },
        {
            "source": "task3",
            "target": "task4",
        },
    ]

    taskgraph = {"graph": graph, "links": links, "nodes": nodes}
    return load_graph(taskgraph).graph


def test_parse_inputs(graph):
    inputs = list()
    expected = inputs
    inputs = graph_io.parse_inputs(graph, inputs)
    assert inputs == expected

    inputs = [{"id": "task1", "name": "a", "value": 10}]
    expected = inputs
    inputs = graph_io.parse_inputs(graph, inputs)
    assert inputs == expected

    inputs = [{"label": "b", "name": "a", "value": 10}]
    expected = [{"id": "task3", "name": "a", "value": 10}]
    inputs = graph_io.parse_inputs(graph, inputs)
    assert inputs == expected

    inputs = [{"label": "a", "name": "a", "value": 10}]
    expected = [
        {"id": "task1", "name": "a", "value": 10},
        {"id": "task2", "name": "a", "value": 10},
    ]
    inputs = graph_io.parse_inputs(graph, inputs)
    assert inputs == expected

    inputs = [{"task_identifier": "Task1", "name": "a", "value": 10}]
    expected = [
        {"id": "task1", "name": "a", "value": 10},
        {"id": "task3", "name": "a", "value": 10},
    ]
    inputs = graph_io.parse_inputs(graph, inputs)
    assert inputs == expected

    inputs = [{"task_identifier": "Task1", "label": "a", "name": "a", "value": 10}]
    expected = [{"id": "task1", "name": "a", "value": 10}]
    inputs = graph_io.parse_inputs(graph, inputs)
    assert inputs == expected

    inputs = [{"name": "a", "value": 10}]
    expected = [{"id": "task1", "name": "a", "value": 10}]
    inputs = graph_io.parse_inputs(graph, inputs)
    assert inputs == expected

    inputs = [{"all": True, "name": "a", "value": 10}]
    expected = [
        {"id": "task1", "name": "a", "value": 10},
        {"id": "task2", "name": "a", "value": 10},
        {"id": "task3", "name": "a", "value": 10},
        {"id": "task4", "name": "a", "value": 10},
    ]
    inputs = graph_io.parse_inputs(graph, inputs)
    assert inputs == expected


def test_update_default_inputs(graph):
    expected = {
        "task1": [{"name": "a", "value": 1}],
        "task2": [{"name": "a", "value": 2}],
        "task3": [{"name": "a", "value": 3}],
        "task4": [{"name": "a", "value": 4}],
    }
    graph_io.update_default_inputs(graph, list())
    for node_id, node_attrs in graph.nodes.items():
        assert node_attrs["default_inputs"] == expected[node_id]

    inputs = [{"id": "task1", "name": "a", "value": 10}]
    expected["task1"] = [{"name": "a", "value": 10}]
    graph_io.update_default_inputs(graph, inputs)
    for node_id, node_attrs in graph.nodes.items():
        assert node_attrs["default_inputs"] == expected[node_id]

    inputs = [{"label": "b", "name": "a", "value": 20}]
    expected["task3"] = [{"name": "a", "value": 20}]
    graph_io.update_default_inputs(graph, inputs)
    for node_id, node_attrs in graph.nodes.items():
        assert node_attrs["default_inputs"] == expected[node_id]

    inputs = [{"label": "a", "name": "a", "value": 30}]
    expected["task1"] = [{"name": "a", "value": 30}]
    expected["task2"] = [{"name": "a", "value": 30}]
    graph_io.update_default_inputs(graph, inputs)
    for node_id, node_attrs in graph.nodes.items():
        assert node_attrs["default_inputs"] == expected[node_id]

    inputs = [{"task_identifier": "Task1", "name": "a", "value": 40}]
    expected["task1"] = [{"name": "a", "value": 40}]
    expected["task3"] = [{"name": "a", "value": 40}]
    graph_io.update_default_inputs(graph, inputs)
    for node_id, node_attrs in graph.nodes.items():
        assert node_attrs["default_inputs"] == expected[node_id]

    inputs = [{"task_identifier": "Task1", "label": "a", "name": "a", "value": 50}]
    expected["task1"] = [{"name": "a", "value": 50}]
    graph_io.update_default_inputs(graph, inputs)
    for node_id, node_attrs in graph.nodes.items():
        assert node_attrs["default_inputs"] == expected[node_id]

    inputs = [{"name": "a", "value": 60}]
    expected["task1"] = [{"name": "a", "value": 60}]
    graph_io.update_default_inputs(graph, inputs)
    for node_id, node_attrs in graph.nodes.items():
        assert node_attrs["default_inputs"] == expected[node_id]

    inputs = [{"all": True, "name": "a", "value": 70}]
    expected["task1"] = [{"name": "a", "value": 70}]
    expected["task2"] = [{"name": "a", "value": 70}]
    expected["task3"] = [{"name": "a", "value": 70}]
    expected["task4"] = [{"name": "a", "value": 70}]
    graph_io.update_default_inputs(graph, inputs)
    for node_id, node_attrs in graph.nodes.items():
        assert node_attrs["default_inputs"] == expected[node_id]


def test_parse_outputs(graph):
    outputs = None
    expected = [{"id": "task4"}]
    outputs = graph_io.parse_outputs(graph, outputs)
    assert outputs == expected

    outputs = [{"all": False}]
    expected = [{"id": "task4"}]
    outputs = graph_io.parse_outputs(graph, outputs)
    assert outputs == expected

    outputs = [{"all": True}]
    expected = [{"id": "task1"}, {"id": "task2"}, {"id": "task3"}, {"id": "task4"}]
    outputs = graph_io.parse_outputs(graph, outputs)
    assert outputs == expected

    outputs = [{"all": False}]
    expected = [{"id": "task4"}]
    outputs = graph_io.parse_outputs(graph, outputs)
    assert outputs == expected
