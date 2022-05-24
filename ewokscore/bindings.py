from typing import Any, Optional, List, Union
from .graph import load_graph as _load_graph
from .graph import TaskGraph
from .graph.execute import sequential
from .graph.graph_io import update_default_inputs
from .events import job_decorator as execute_graph_decorator

__all__ = [
    "execute_graph",
    "load_graph",
    "save_graph",
    "convert_graph",
    "graph_is_supported",
    "execute_graph_decorator",
]


def load_graph(
    graph: Any, inputs: Optional[List[dict]] = None, **load_options
) -> TaskGraph:
    taskgraph = _load_graph(source=graph, **load_options)
    if inputs:
        update_default_inputs(taskgraph.graph, inputs)
    return taskgraph


def save_graph(graph: TaskGraph, destination, **save_options) -> Union[str, dict]:
    return graph.dump(destination, **save_options)


def convert_graph(
    source,
    destination,
    inputs: Optional[List[dict]] = None,
    load_options: Optional[dict] = None,
    save_options: Optional[dict] = None,
) -> Union[str, dict]:
    if load_options is None:
        load_options = dict()
    if save_options is None:
        save_options = dict()
    graph = load_graph(source, inputs=inputs, **load_options)
    return save_graph(graph, destination, **save_options)


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


def graph_is_supported(graph: TaskGraph) -> bool:
    return not graph.is_cyclic and not graph.has_conditional_links
