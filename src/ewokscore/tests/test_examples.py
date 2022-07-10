from typing import Iterable, Optional, Tuple
import pytest

from ewokscore import execute_graph
from ewokscore import load_graph
from ewokscore import convert_graph
from ewokscore import graph_is_supported
from ewokscore.graph.analysis import start_nodes

from .examples.graphs import graph_names
from .examples.graphs import get_graph
from .utils.results import assert_execute_graph_default_result
from .utils.results import assert_execute_graph_tasks
from .utils.show import show_graph


@pytest.mark.parametrize("graph_name", graph_names())
@pytest.mark.parametrize("scheme", (None, "json", "nexus"))
def test_execute_graph(graph_name, scheme, tmpdir):
    graph, expected = get_graph(graph_name)
    ewoksgraph = load_graph(graph)
    if scheme:
        varinfo = {"root_uri": str(tmpdir), "scheme": scheme}
    else:
        varinfo = None
    if not graph_is_supported(ewoksgraph):
        with pytest.raises(RuntimeError):
            execute_graph(ewoksgraph, varinfo=varinfo)
        return

    result = execute_graph(ewoksgraph, varinfo=varinfo)
    assert_execute_graph_default_result(ewoksgraph, result, expected, varinfo)
    result = execute_graph(ewoksgraph, varinfo=varinfo, output_tasks=True)
    assert_execute_graph_tasks(ewoksgraph, result, expected, varinfo)


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
    assert start_nodes(ewoksgraph.graph) == {"task1", "task2"}

    graph, _ = get_graph("acyclic2")
    ewoksgraph = load_graph(graph)
    assert start_nodes(ewoksgraph.graph) == {"task1"}

    graph, _ = get_graph("cyclic1")
    ewoksgraph = load_graph(graph)
    assert start_nodes(ewoksgraph.graph) == {"task1"}

    graph, _ = get_graph("triangle1")
    ewoksgraph = load_graph(graph)
    assert start_nodes(ewoksgraph.graph) == {"task1"}


@pytest.mark.parametrize("graph_name", graph_names())
@pytest.mark.parametrize(
    "representation", (None, "json", "json_dict", "json_string", "yaml")
)
def test_serialize_graph(graph_name, representation, tmpdir):
    graph, _ = get_graph(graph_name)
    ewoksgraph = load_graph(graph)
    if representation == "yaml":
        destination = str(tmpdir / "file.yml")
    elif representation == "json":
        destination = str(tmpdir / "file.json")
    else:
        destination = None
    inmemorydump = ewoksgraph.dump(destination, representation=representation)

    if destination:
        source = destination
    else:
        source = inmemorydump
    ewoksgraph2 = load_graph(source, representation=representation)

    assert ewoksgraph == ewoksgraph2


@pytest.mark.parametrize("graph_name", graph_names())
def test_convert_graph(graph_name, tmpdir):
    graph, _ = get_graph(graph_name)
    ewoksgraph = load_graph(graph)
    assert_convert_graph(convert_graph, ewoksgraph, tmpdir)


def assert_convert_graph(
    convert_graph,
    ewoksgraph,
    tmpdir,
    representations: Optional[Iterable[Tuple[dict, dict, Optional[str]]]] = None,
):
    """All graph `representations` need to be known by `convert_graph`. It will always
    test the basic representations (e.g. json and yaml) in addition to the provided
    `representations`.

    The tuple-items in `representations` are: load options, save options, file extension.
    """
    non_serialized_representation = dict(), dict(), None
    conversion_chain = [
        non_serialized_representation,
        (dict(), {"representation": "json"}, "json"),
        (dict(), {"representation": "yaml"}, "yaml"),
        (dict(), {"representation": "json_dict"}, None),
        (dict(), {"representation": "json_string"}, None),
    ]
    if representations:
        conversion_chain.extend(representations)
    conversion_chain.append(non_serialized_representation)
    source = ewoksgraph
    for convert_from, convert_to in zip(conversion_chain[:-1], conversion_chain[1:]):
        load_options, _, _ = convert_from
        _, save_options, fileext = convert_to
        if fileext:
            destination = str(tmpdir / f"file.{fileext}")
        else:
            destination = None
        result = convert_graph(
            source,
            destination,
            load_options=load_options,
            save_options=save_options,
        )
        if fileext:
            source = destination
        else:
            source = result

    ewoksgraph2 = load_graph(source)
    try:
        assert ewoksgraph == ewoksgraph2
    except AssertionError:
        show_graph(ewoksgraph, plot=False)
        show_graph(ewoksgraph2, plot=False)
        raise
