import pytest
from ewokscore.graph import load_graph
from ewokscore.graph.analysis import link_is_required


def test_required_links():
    nodes = [
        {"id": "source1", "task_type": "method", "task_identifier": "dummy"},
        {"id": "source2a", "task_type": "method", "task_identifier": "dummy"},
        {"id": "source2b", "task_type": "method", "task_identifier": "dummy"},
        {"id": "target", "task_type": "method", "task_identifier": "dummy"},
    ]
    links = [
        {"source": "source1", "target": "target"},
        {"source": "source2a", "target": "source2b"},
        {"source": "source2b", "target": "target"},
    ]
    taskgraph = load_graph({"graph": {"id": "test"}, "nodes": nodes, "links": links})
    assert link_is_required(taskgraph.graph, "source1", "target")
    assert link_is_required(taskgraph.graph, "source2a", "source2b")
    assert link_is_required(taskgraph.graph, "source2b", "target")

    links[0]["conditions"] = [{"source_output": "a", "value": 1}]
    taskgraph = load_graph({"graph": {"id": "test"}, "nodes": nodes, "links": links})
    assert not link_is_required(taskgraph.graph, "source1", "target")
    assert link_is_required(taskgraph.graph, "source2a", "source2b")
    assert link_is_required(taskgraph.graph, "source2b", "target")
    links[0].pop("conditions")

    links[1]["conditions"] = [{"source_output": "a", "value": 1}]
    taskgraph = load_graph({"graph": {"id": "test"}, "nodes": nodes, "links": links})
    assert link_is_required(taskgraph.graph, "source1", "target")
    assert not link_is_required(taskgraph.graph, "source2a", "source2b")
    assert not link_is_required(taskgraph.graph, "source2b", "target")
    links[1].pop("conditions")

    links[1]["conditions"] = [{"source_output": "a", "value": 1}]
    links[1]["required"] = True
    taskgraph = load_graph({"graph": {"id": "test"}, "nodes": nodes, "links": links})
    assert link_is_required(taskgraph.graph, "source1", "target")
    assert link_is_required(taskgraph.graph, "source2a", "source2b")
    assert link_is_required(taskgraph.graph, "source2b", "target")
    links[1].pop("conditions")

    links[2]["conditions"] = [{"source_output": "a", "value": 1}]
    taskgraph = load_graph({"graph": {"id": "test"}, "nodes": nodes, "links": links})
    assert link_is_required(taskgraph.graph, "source1", "target")
    assert link_is_required(taskgraph.graph, "source2a", "source2b")
    assert not link_is_required(taskgraph.graph, "source2b", "target")
    links[2].pop("conditions")

    links[2]["conditions"] = [{"source_output": "a", "value": 1}]
    links[2]["required"] = True
    taskgraph = load_graph({"graph": {"id": "test"}, "nodes": nodes, "links": links})
    assert link_is_required(taskgraph.graph, "source1", "target")
    assert link_is_required(taskgraph.graph, "source2a", "source2b")
    assert link_is_required(taskgraph.graph, "source2b", "target")
    links[2].pop("conditions")


def test_wrong_argument_definitions():
    nodes = [
        {"id": "source1", "task_type": "method", "task_identifier": "dummy"},
        {"id": "source2", "task_type": "method", "task_identifier": "dummy"},
        {"id": "target", "task_type": "method", "task_identifier": "dummy"},
    ]
    links = [
        {
            "source": "source1",
            "target": "target",
            "data_mapping": [{"source_output": "a", "target_input": "a"}],
        },
        {
            "source": "source2",
            "target": "target",
            "data_mapping": [{"source_output": "a", "target_input": "a"}],
        },
    ]
    graph = {"graph": {"id": "test"}, "nodes": nodes, "links": links}
    with pytest.raises(ValueError):
        load_graph(graph)

    links[0]["conditions"] = [{"source_output": "a", "value": 1}]
    load_graph(graph)

    links[0]["required"] = True
    with pytest.raises(ValueError):
        load_graph(graph)
