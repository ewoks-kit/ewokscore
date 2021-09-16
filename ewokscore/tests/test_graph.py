import pytest
from ewokscore.graph import load_graph


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
    graph = load_graph({"nodes": nodes, "links": links})
    assert graph.link_is_required("source1", "target")
    assert graph.link_is_required("source2a", "source2b")
    assert graph.link_is_required("source2b", "target")

    links[0]["conditions"] = [{"source_output": "a", "value": 1}]
    graph = load_graph({"nodes": nodes, "links": links})
    assert not graph.link_is_required("source1", "target")
    assert graph.link_is_required("source2a", "source2b")
    assert graph.link_is_required("source2b", "target")
    links[0].pop("conditions")

    links[1]["conditions"] = [{"source_output": "a", "value": 1}]
    graph = load_graph({"nodes": nodes, "links": links})
    assert graph.link_is_required("source1", "target")
    assert not graph.link_is_required("source2a", "source2b")
    assert not graph.link_is_required("source2b", "target")
    links[1].pop("conditions")

    links[1]["conditions"] = [{"source_output": "a", "value": 1}]
    links[1]["required"] = True
    graph = load_graph({"nodes": nodes, "links": links})
    assert graph.link_is_required("source1", "target")
    assert graph.link_is_required("source2a", "source2b")
    assert graph.link_is_required("source2b", "target")
    links[1].pop("conditions")

    links[2]["conditions"] = [{"source_output": "a", "value": 1}]
    graph = load_graph({"nodes": nodes, "links": links})
    assert graph.link_is_required("source1", "target")
    assert graph.link_is_required("source2a", "source2b")
    assert not graph.link_is_required("source2b", "target")
    links[2].pop("conditions")

    links[2]["conditions"] = [{"source_output": "a", "value": 1}]
    links[2]["required"] = True
    graph = load_graph({"nodes": nodes, "links": links})
    assert graph.link_is_required("source1", "target")
    assert graph.link_is_required("source2a", "source2b")
    assert graph.link_is_required("source2b", "target")
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
            "data_mapping": [{"target_input": "a", "source_output": "a"}],
        },
        {
            "source": "source2",
            "target": "target",
            "data_mapping": [{"target_input": "a", "source_output": "a"}],
        },
    ]
    graph = {"nodes": nodes, "links": links}
    with pytest.raises(ValueError):
        load_graph(graph)

    links[0]["conditions"] = [{"source_output": "a", "value": 1}]
    load_graph(graph)

    links[0]["required"] = True
    with pytest.raises(ValueError):
        load_graph(graph)
