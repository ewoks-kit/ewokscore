import pytest
import itertools
from .examples.graphs import graph_names
from .examples.graphs import get_graph
from .utils import assert_taskgraph_result
from ewokscore import load_graph


@pytest.mark.parametrize(
    "graph_name,persist", itertools.product(graph_names(), (True, False))
)
def test_execute_graph(graph_name, persist, tmpdir):
    g, expected = get_graph(graph_name)
    ewoksgraph = load_graph(g)
    if persist:
        varinfo = {"root_uri": str(tmpdir)}
    else:
        varinfo = None
    if ewoksgraph.is_cyclic or ewoksgraph.has_conditional_links:
        with pytest.raises(RuntimeError):
            ewoksgraph.execute(varinfo=varinfo)
    else:
        tasks = ewoksgraph.execute(varinfo=varinfo)
        assert_taskgraph_result(ewoksgraph, expected, tasks=tasks)
        if persist:
            assert_taskgraph_result(ewoksgraph, expected, varinfo=varinfo)


def test_graph_cyclic():
    g, _ = get_graph("empty")
    taskgraph = load_graph(g)
    assert not taskgraph.is_cyclic
    g, _ = get_graph("acyclic1")
    taskgraph = load_graph(g)
    assert not taskgraph.is_cyclic
    g, _ = get_graph("cyclic1")
    taskgraph = load_graph(g)
    assert taskgraph.is_cyclic


def test_start_nodes():
    g, _ = get_graph("acyclic1")
    taskgraph = load_graph(g)
    assert taskgraph.start_nodes() == {"task1", "task2"}

    g, _ = get_graph("acyclic2")
    taskgraph = load_graph(g)
    assert taskgraph.start_nodes() == {"task1"}

    g, _ = get_graph("cyclic1")
    taskgraph = load_graph(g)
    assert taskgraph.start_nodes() == {"task1"}

    g, _ = get_graph("triangle1")
    taskgraph = load_graph(g)
    assert taskgraph.start_nodes() == {"task1"}
