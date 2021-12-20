from typing import Optional, List
from .graph import load_graph


def execute_graph(
    graph,
    inputs: Optional[List[dict]] = None,
    load_options: Optional[dict] = None,
    **execute_options
):
    if load_options is None:
        load_options = dict()
    graph = load_graph(source=graph, **load_options)
    if inputs:
        graph.update_default_inputs(inputs)
    return graph.execute(**execute_options)
