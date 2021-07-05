import pytest
from .examples import graphs
from .utils import assert_taskgraph_result
from ewokscore import load_graph


def test_graph_cyclic():
    g, _ = graphs.empty_graph()
    taskgraph = load_graph(g)
    assert not taskgraph.is_cyclic
    g, _ = graphs.acyclic_graph1()
    taskgraph = load_graph(g)
    assert not taskgraph.is_cyclic
    g, _ = graphs.cyclic_graph1()
    taskgraph = load_graph(g)
    assert taskgraph.is_cyclic


def test_acyclic_execution(tmpdir):
    # Naive sequential task scheduler
    g, expected = graphs.acyclic_graph1()
    taskgraph = load_graph(g)
    varinfo = {"root_uri": str(tmpdir)}
    taskgraph.execute(varinfo=varinfo)
    assert_taskgraph_result(taskgraph, expected, varinfo)


def test_cyclic_execution(tmpdir):
    g, _ = graphs.cyclic_graph1()
    taskgraph = load_graph(g)
    varinfo = {"root_uri": str(tmpdir)}
    with pytest.raises(RuntimeError):
        taskgraph.execute(varinfo=varinfo)


def test_start_nodes():
    g, _ = graphs.acyclic_graph1()
    taskgraph = load_graph(g)
    assert taskgraph.start_nodes() == {"task1", "task2"}

    g, _ = graphs.acyclic_graph2()
    taskgraph = load_graph(g)
    assert taskgraph.start_nodes() == {"task1"}

    g, _ = graphs.cyclic_graph1()
    taskgraph = load_graph(g)
    assert taskgraph.start_nodes() == {"task1"}

    g, _ = graphs.cyclic_graph2()
    taskgraph = load_graph(g)
    assert taskgraph.start_nodes() == {"task1"}
