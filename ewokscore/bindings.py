from typing import Optional
from .graph import load_graph


def execute_graph(graph, load_options: Optional[dict] = None, **execute_options):
    """
    :param graph: graph to be executed
    :param Optional[dict] load_options: options to provide to the `load_graph` function (and as a consequence to the `TaskGraph.load` as `root_dir`)
    :param execute_options: options to provide to the Graph.execute function as `varinfo` or `raise_on_error`
    """
    if load_options is None:
        load_options = dict()
    graph = load_graph(source=graph, **load_options)
    return graph.execute(**execute_options)
