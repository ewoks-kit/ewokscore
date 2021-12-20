import pytest
from .examples.graphs import graph_names
from .examples.graphs import get_graph
from .utils.results import assert_execute_graph_all_tasks
from .utils.results import assert_execute_graph_tasks
from .utils.results import filter_expected_results
from ewokscore import load_graph


@pytest.mark.parametrize("graph_name", graph_names())
@pytest.mark.parametrize("scheme", (None, "json", "nexus"))
def test_execute_graph(graph_name, scheme, tmpdir):
    graph, expected = get_graph(graph_name)
    ewoksgraph = load_graph(graph)
    if scheme:
        varinfo = {"root_uri": str(tmpdir), "scheme": scheme}
    else:
        varinfo = None
    if ewoksgraph.is_cyclic or ewoksgraph.has_conditional_links:
        with pytest.raises(RuntimeError):
            ewoksgraph.execute(varinfo=varinfo)
        return

    result = ewoksgraph.execute(varinfo=varinfo, results_of_all_nodes=True)
    assert_all_results(ewoksgraph, result, expected, varinfo)
    result = ewoksgraph.execute(varinfo=varinfo, results_of_all_nodes=False)
    assert_end_results(ewoksgraph, result, expected, varinfo)


def assert_all_results(ewoksgraph, result, expected, varinfo):
    if varinfo:
        scheme = varinfo.get("scheme")
    else:
        scheme = None
    assert_execute_graph_all_tasks(ewoksgraph, expected, execute_graph_result=result)
    if scheme:
        assert_execute_graph_all_tasks(ewoksgraph, expected, varinfo=varinfo)


def assert_end_results(ewoksgraph, result, expected, varinfo):
    expected = filter_expected_results(ewoksgraph, expected, end_only=True)
    assert_execute_graph_tasks(result, expected, varinfo=varinfo)


def test_graph_cyclic():
    graph, _ = get_graph("empty")
    ewoksgraph = load_graph(graph)
    assert not ewoksgraph.is_cyclic
    graph, _ = get_graph("acyclic1")
    ewoksgraph = load_graph(graph)
    assert not ewoksgraph.is_cyclic
    graph, _ = get_graph("cyclic1")
    ewoksgraph = load_graph(graph)
    assert ewoksgraph.is_cyclic


def test_start_nodes():
    graph, _ = get_graph("acyclic1")
    ewoksgraph = load_graph(graph)
    assert ewoksgraph.start_nodes() == {"task1", "task2"}

    graph, _ = get_graph("acyclic2")
    ewoksgraph = load_graph(graph)
    assert ewoksgraph.start_nodes() == {"task1"}

    graph, _ = get_graph("cyclic1")
    ewoksgraph = load_graph(graph)
    assert ewoksgraph.start_nodes() == {"task1"}

    graph, _ = get_graph("triangle1")
    ewoksgraph = load_graph(graph)
    assert ewoksgraph.start_nodes() == {"task1"}
