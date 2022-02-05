from typing import Optional, List
from .graph import load_graph
from .graph.execute import sequential
from .graph.graph_io import update_default_inputs


def execute_graph(
    graph,
    inputs: Optional[List[dict]] = None,
    load_options: Optional[dict] = None,
    **execute_options
):
    if load_options is None:
        load_options = dict()
    taskgraph = load_graph(source=graph, **load_options)
    if inputs:
        update_default_inputs(taskgraph.graph, inputs)
    return sequential.execute_graph(taskgraph.graph, **execute_options)
