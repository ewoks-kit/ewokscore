import networkx
import pytest

from ...graph import load_graph
from ...graph._analysis import GraphAnalysis
from . import _common


def test_analysis_is_cached_per_graph():
    taskgraph = load_graph(
        {
            "graph": {"id": "test", "schema_version": "1.2"},
            "nodes": [_common.node("a"), _common.node("b")],
            "links": _common.chain("a", "b"),
        }
    )

    assert taskgraph.analysis is taskgraph.analysis
    assert taskgraph.analysis.start_nodes() == {"a"}

    # The graph is frozen after loading: structural changes...
    with pytest.raises(networkx.NetworkXError):
        taskgraph.graph.add_node("c", **_common.node("c"))
    with pytest.raises(networkx.NetworkXError):
        taskgraph.graph.remove_node("a")
    with pytest.raises(networkx.NetworkXError):
        taskgraph.graph.add_edge("b", "a")
    with pytest.raises(networkx.NetworkXError):
        taskgraph.graph.remove_edge("a", "b")

    # ...and attribute changes are rejected too, so `analysis` cannot go stale
    with pytest.raises(TypeError):
        taskgraph.graph.nodes["b"]["force_start_node"] = True
    with pytest.raises(TypeError):
        del taskgraph.graph.nodes["b"]["task_identifier"]
    with pytest.raises(TypeError):
        taskgraph.graph["a"]["b"]["conditions"] = _common.TRUE
    with pytest.raises(TypeError):
        taskgraph.graph.graph["label"] = "renamed"
    with pytest.raises(TypeError):
        taskgraph.graph.graph = {}

    # ...except for a node's `default_inputs`, which `update_default_inputs`
    # needs to set at execution time
    taskgraph.graph.nodes["b"]["default_inputs"] = [{"name": "value", "value": 1}]
    assert taskgraph.graph.nodes["b"]["default_inputs"] == [
        {"name": "value", "value": 1}
    ]


def test_deep_chain_has_no_recursion_limit():
    """Nothing in the analysis may recurse per node."""
    num_nodes = 5000
    graph = networkx.DiGraph()
    graph.add_edges_from((f"n{i}", f"n{i + 1}") for i in range(num_nodes - 1))
    analysis = GraphAnalysis(graph)
    last_id = f"n{num_nodes - 1}"

    assert len(analysis.ancestors(last_id)) == num_nodes - 1
    assert len(analysis.descendants("n0")) == num_nodes - 1
    assert len(set(analysis.node_pure_descendants("n0"))) == num_nodes - 1
    assert analysis.link_is_required("n0", "n1")
    assert analysis.start_nodes() == {"n0"}
    assert analysis.end_nodes() == {last_id}
    assert len(list(analysis.topological_sort())) == num_nodes
