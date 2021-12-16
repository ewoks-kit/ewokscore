import pytest
from .examples.graphs import graph_names
from .examples.graphs import get_graph
from .utils import assert_execute_graph_all_tasks
from .utils import assert_execute_graph_tasks
from ewokscore import load_graph


@pytest.mark.parametrize("graph_name", graph_names())
@pytest.mark.parametrize("scheme", (None, "json", "nexus"))
def test_execute_graph(graph_name, scheme, tmpdir):
    g, expected = get_graph(graph_name)
    ewoksgraph = load_graph(g)
    if scheme:
        varinfo = {"root_uri": str(tmpdir), "scheme": scheme}
    else:
        varinfo = None
    if ewoksgraph.is_cyclic or ewoksgraph.has_conditional_links:
        with pytest.raises(RuntimeError):
            ewoksgraph.execute(varinfo=varinfo)
    else:
        result = ewoksgraph.execute(varinfo=varinfo, results_of_all_nodes=True)
        assert_execute_graph_all_tasks(
            ewoksgraph, expected, execute_graph_result=result
        )
        if scheme:
            assert_execute_graph_all_tasks(ewoksgraph, expected, varinfo=varinfo)

        end_tasks = ewoksgraph.execute(varinfo=varinfo, results_of_all_nodes=False)
        end_nodes = ewoksgraph.end_nodes()
        assert end_tasks.keys() == end_nodes
        expected = {k: v for k, v in expected.items() if k in end_nodes}
        assert_execute_graph_tasks(end_tasks, expected, varinfo=varinfo)


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
