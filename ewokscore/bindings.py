from typing import Optional, List
from .graph import load_graph as _load_graph
from .graph import TaskGraph
from .graph.execute import sequential
from .graph.graph_io import update_default_inputs
from .events import job_decorator as execute_graph_decorator


def load_graph(graph, inputs: Optional[List[dict]] = None, **load_options) -> TaskGraph:
    taskgraph = _load_graph(source=graph, **load_options)
    if inputs:
        update_default_inputs(taskgraph.graph, inputs)
    return taskgraph


@execute_graph_decorator()
def execute_graph(
    graph,
    inputs: Optional[List[dict]] = None,
    load_options: Optional[dict] = None,
    **execute_options
):
    if load_options is None:
        load_options = dict()
    taskgraph = load_graph(graph, inputs=inputs, **load_options)
    return sequential.execute_graph(taskgraph.graph, **execute_options)
