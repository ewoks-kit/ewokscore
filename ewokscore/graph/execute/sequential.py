from typing import Optional, Dict, List, Union, Any
from collections import Counter
import networkx

from ...node import NodeIdType
from ...task import Task
from ...inittask import instantiate_task as _instantiate_task
from ...inittask import add_dynamic_inputs
from .. import analysis
from .. import graph_io
from ... import events


def instantiate_task(graph: networkx.DiGraph, node_id: NodeIdType, **kw) -> Task:
    """Named arguments are dynamic input and Variable config.
    Default input from the persistent representation are added internally.
    """
    # Dynamic input has priority over default input
    nodeattrs = graph.nodes[node_id]
    return _instantiate_task(node_id, nodeattrs, **kw)


def instantiate_task_static(
    graph: networkx.DiGraph,
    node_id: NodeIdType,
    tasks: Optional[Dict[Task, int]] = None,
    varinfo: Optional[dict] = None,
    execinfo: Optional[dict] = None,
    evict_result_counter: Optional[Dict[NodeIdType, int]] = None,
) -> Task:
    """Instantiate destination task while no access to the dynamic inputs.
    Side effect: `tasks` will contain all predecessors.
    """
    if analysis.graph_is_cyclic(graph):
        raise RuntimeError("cannot execute cyclic graphs with ewokscore")
    if tasks is None:
        tasks = dict()
    if evict_result_counter is None:
        evict_result_counter = dict()
    # Input from previous tasks (instantiate them if needed)
    dynamic_inputs = dict()
    for source_id in analysis.node_predecessors(graph, node_id):
        source_task = tasks.get(source_id, None)
        if source_task is None:
            source_task = instantiate_task_static(
                graph,
                source_id,
                tasks=tasks,
                varinfo=varinfo,
                execinfo=execinfo,
                evict_result_counter=evict_result_counter,
            )
        link_attrs = graph[source_id][node_id]
        add_dynamic_inputs(
            dynamic_inputs,
            link_attrs,
            source_task.output_variables,
            source_id=source_id,
            target_id=node_id,
        )
        # Evict intermediate results
        if evict_result_counter:
            evict_result_counter[source_id] -= 1
            if evict_result_counter[source_id] == 0:
                tasks.pop(source_id)
    # Instantiate the requested task
    target_task = instantiate_task(
        graph, node_id, inputs=dynamic_inputs, varinfo=varinfo, execinfo=execinfo
    )
    tasks[node_id] = target_task
    return target_task


def successor_counter(graph: networkx.DiGraph) -> Dict[NodeIdType, int]:
    nsuccessor = Counter()
    for edge in graph.edges:
        nsuccessor[edge[0]] += 1
    return nsuccessor


def execute_graph(
    graph: networkx.DiGraph,
    varinfo: Optional[dict] = None,
    execinfo: Optional[dict] = None,
    raise_on_error: Optional[bool] = True,
    outputs: Optional[List[dict]] = None,
    merge_outputs: Optional[bool] = True,
    output_tasks: Optional[bool] = False,
) -> Union[Dict[NodeIdType, Task], Dict[str, Any]]:
    """Sequential execution of DAGs.

    When `output_tasks` is `True` the arguments `outputs` and `merge_outputs`
    are ignored and instead of returning output values, it returns `Task` instances.
    This was introduced for testing.
    """
    with events.workflow_context(execinfo, workflow=graph) as execinfo:
        if analysis.graph_is_cyclic(graph):
            raise RuntimeError("cannot execute cyclic graphs")
        if analysis.graph_has_conditional_links(graph):
            raise RuntimeError("cannot execute graphs with conditional links")

        # Pepare containers for local state
        tasks = dict()
        if output_tasks:
            output_values = None
            evict_result_counter = None
        else:
            outputs = graph_io.parse_outputs(graph, outputs)
            output_values = dict()
            evict_result_counter = successor_counter(graph)

        # Execute in topological order
        for node_id in analysis.topological_sort(graph):
            task = instantiate_task_static(
                graph,
                node_id,
                tasks=tasks,
                varinfo=varinfo,
                execinfo=execinfo,
                evict_result_counter=evict_result_counter,
            )
            task.execute(
                raise_on_error=raise_on_error,
                cleanup_references=evict_result_counter is not None,
            )
            if execinfo:
                execinfo.setdefault("exception", task.exception)
            if not output_tasks:
                graph_io.add_output_values(
                    output_values, node_id, task, outputs, merge_outputs=merge_outputs
                )

        # Return results or Task instances
        if output_tasks:
            return tasks
        else:
            return output_values
