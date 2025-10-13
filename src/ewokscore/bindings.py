from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from .events import job_decorator as execute_graph_decorator
from .graph import TaskGraph
from .graph import load_graph as _load_graph
from .graph.execute import sequential
from .graph.graph_io import update_default_inputs
from .graph.serialize import GraphRepresentation
from .node import NodeIdType
from .task import Task

__all__ = [
    "execute_graph",
    "load_graph",
    "save_graph",
    "convert_graph",
    "graph_is_supported",
    "execute_graph_decorator",
]


def load_graph(
    graph: Any,
    inputs: Optional[List[dict]] = None,
    representation: Optional[Union[GraphRepresentation, str]] = None,
    root_dir: Optional[Union[str, Path]] = None,
    root_module: Optional[str] = None,
) -> TaskGraph:
    taskgraph = _load_graph(
        source=graph,
        representation=representation,
        root_dir=root_dir,
        root_module=root_module,
    )
    if inputs:
        update_default_inputs(taskgraph.graph, inputs)
    return taskgraph


def save_graph(
    graph: TaskGraph,
    destination,
    representation: Optional[Union[GraphRepresentation, str]] = None,
    **save_options,
) -> Union[str, dict]:
    return graph.dump(destination, representation=representation, **save_options)


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


@execute_graph_decorator(engine="core")
def execute_graph(
    graph,
    inputs: Optional[List[dict]] = None,
    load_options: Optional[dict] = None,
    varinfo: Optional[dict] = None,
    execinfo: Optional[dict] = None,
    task_options: Optional[dict] = None,
    raise_on_error: Optional[bool] = True,
    outputs: Optional[List[dict]] = None,
    merge_outputs: Optional[bool] = True,
    output_tasks: Optional[bool] = False,
) -> Union[Dict[NodeIdType, Task], Dict[str, Any]]:
    if load_options is None:
        load_options = dict()
    taskgraph = load_graph(graph, inputs=inputs, **load_options)
    return sequential.execute_graph(
        taskgraph.graph,
        varinfo=varinfo,
        execinfo=execinfo,
        task_options=task_options,
        raise_on_error=raise_on_error,
        outputs=outputs,
        merge_outputs=merge_outputs,
        output_tasks=output_tasks,
    )


def graph_is_supported(graph: TaskGraph) -> bool:
    return not graph.is_cyclic and not graph.has_conditional_links
