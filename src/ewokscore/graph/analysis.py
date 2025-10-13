from collections import defaultdict
from typing import Dict
from typing import Iterator
from typing import Set

import networkx

from ..inittask import get_task_class
from ..node import NodeIdType


def graph_is_cyclic(graph: networkx.DiGraph) -> bool:
    return not networkx.is_directed_acyclic_graph(graph)


def graph_has_conditional_links(graph: networkx.DiGraph) -> bool:
    for attrs in graph.edges.values():
        if attrs.get("conditions") or attrs.get("on_error"):
            return True
    return False


def node_successors(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
) -> Iterator[NodeIdType]:
    if include_filter:
        yield from iter_downstream_nodes(
            graph, node_id, recursive=False, **include_filter
        )
    else:
        yield from graph.successors(node_id)


def node_descendants(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
) -> Iterator[NodeIdType]:
    yield from iter_downstream_nodes(graph, node_id, recursive=True, **include_filter)


def node_predecessors(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
) -> Iterator[NodeIdType]:
    if include_filter:
        yield from iter_upstream_nodes(
            graph, node_id, recursive=False, **include_filter
        )
    else:
        yield from graph.predecessors(node_id)


def node_ancestors(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
) -> Iterator[NodeIdType]:
    yield from iter_upstream_nodes(graph, node_id, recursive=True, **include_filter)


def iterator_has_items(iterator):
    try:
        next(iterator)
        return True
    except StopIteration:
        return False


def node_has_successors(graph: networkx.DiGraph, node_id: NodeIdType, **include_filter):
    return iterator_has_items(node_successors(graph, node_id, **include_filter))


def node_has_descendants(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
):
    return iterator_has_items(node_descendants(graph, node_id, **include_filter))


def node_has_predecessors(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
):
    return iterator_has_items(node_predecessors(graph, node_id, **include_filter))


def node_has_ancestors(graph: networkx.DiGraph, node_id: NodeIdType, **include_filter):
    return iterator_has_items(node_ancestors(graph, node_id, **include_filter))


def iter_downstream_nodes(
    graph: networkx.DiGraph, node_id: NodeIdType, **kw
) -> Iterator[NodeIdType]:
    yield from _iter_nodes(graph, node_id, upstream=False, **kw)


def iter_upstream_nodes(
    graph: networkx.DiGraph, node_id: NodeIdType, **kw
) -> Iterator[NodeIdType]:
    yield from _iter_nodes(graph, node_id, upstream=True, **kw)


def _iter_nodes(
    graph: networkx.DiGraph,
    node_id: NodeIdType,
    upstream=False,
    recursive=False,
    _visited=None,
    **include_filter,
) -> Iterator[NodeIdType]:
    """Recursion is not stopped by the node or link filters.
    Recursion is stopped by either not having any successors/predecessors
    or encountering a node that has been visited already.
    The original node on which we start iterating is never yielded.
    """
    if recursive:
        if _visited is None:
            _visited = set()
        elif node_id in _visited:
            return
        _visited.add(node_id)
    if upstream:
        iter_next_nodes = graph.predecessors
    else:
        iter_next_nodes = graph.successors
    if not include_filter.get("parsed"):
        include_filter = {f"_{k}": v for k, v in include_filter.items()}
        include_filter["parsed"] = True
    for next_id in iter_next_nodes(node_id):
        node_is_included = _filter_node(graph, next_id, **include_filter)
        if upstream:
            link_is_included = _filter_link(graph, next_id, node_id, **include_filter)
        else:
            link_is_included = _filter_link(graph, node_id, next_id, **include_filter)
        if node_is_included and link_is_included:
            yield next_id
        if recursive:
            yield from _iter_nodes(
                graph,
                next_id,
                upstream=upstream,
                recursive=True,
                _visited=_visited,
                **include_filter,
            )


def _filter_node(
    graph: networkx.DiGraph,
    node_id: NodeIdType,
    _node_filter=None,
    _node_has_predecessors=None,
    _node_has_successors=None,
    _node_has_error_handlers=None,
    **_,
) -> bool:
    """Filters are combined with the logical AND"""
    if callable(_node_filter):
        if not _node_filter(node_id):
            return False
    if _node_has_predecessors is not None:
        if node_has_predecessors(graph, node_id) != _node_has_predecessors:
            return False
    if _node_has_successors is not None:
        if node_has_successors(graph, node_id) != _node_has_successors:
            return False
    if _node_has_error_handlers is not None:
        if node_has_error_handlers(graph, node_id) != _node_has_error_handlers:
            return False
    return True


def _filter_link(
    graph: networkx.DiGraph,
    source_id: NodeIdType,
    target_id: NodeIdType,
    _link_filter=None,
    _link_has_on_error=None,
    _link_has_conditions=None,
    _link_is_conditional=None,
    _link_has_required=None,
    **_,
) -> bool:
    """Filters are combined with the logical AND"""
    if callable(_link_filter):
        if not _link_filter(source_id, target_id):
            return False
    if _link_has_on_error is not None:
        if link_has_on_error(graph, source_id, target_id) != _link_has_on_error:
            return False
    if _link_has_conditions is not None:
        if link_has_conditions(graph, source_id, target_id) != _link_has_conditions:
            return False
    if _link_is_conditional is not None:
        if link_is_conditional(graph, source_id, target_id) != _link_is_conditional:
            return False
    if _link_has_required is not None:
        if link_has_required(graph, source_id, target_id) != _link_has_required:
            return False
    return True


def link_has_conditions(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    link_attrs = graph[source_id][target_id]
    return bool(link_attrs.get("conditions", False))


def link_has_on_error(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    link_attrs = graph[source_id][target_id]
    return bool(link_attrs.get("on_error", False))


def link_has_required(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    link_attrs = graph[source_id][target_id]
    return bool(link_attrs.get("required", False))


def link_is_conditional(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    link_attrs = graph[source_id][target_id]
    return bool(
        link_attrs.get("on_error", False) or link_attrs.get("conditions", False)
    )


def link_is_required(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    if link_has_required(graph, source_id, target_id):
        return True
    if link_is_conditional(graph, source_id, target_id):
        return False
    return node_is_required(graph, source_id)


def node_is_required(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    not_required = node_has_ancestors(
        graph, node_id, link_has_required=False, link_is_conditional=True
    )
    not_required |= node_has_ancestors(graph, node_id, node_has_error_handlers=True)
    return not not_required


def node_has_error_handlers(graph: networkx.DiGraph, node_id: NodeIdType):
    return node_has_successors(graph, node_id, link_has_on_error=True)


def required_predecessors(
    graph: networkx.DiGraph, target_id: NodeIdType
) -> Iterator[NodeIdType]:
    for source_id in node_predecessors(graph, target_id):
        if link_is_required(graph, source_id, target_id):
            yield source_id


def has_required_predecessors(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    return iterator_has_items(required_predecessors(graph, node_id))


def has_required_static_inputs(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    """Returns True when the default inputs cover all required inputs."""
    node_attrs = graph.nodes[node_id]
    if node_attrs.get("task_type", None) != "class":
        # Tasks that are not `class` (e.g. `method` and `script`)
        # always have an empty `required_input_names`
        # although they may have required input.
        return False
    taskclass = get_task_class(node_id, node_attrs)
    static_inputs = {d["name"] for d in node_attrs.get("default_inputs", list())}
    return not (set(taskclass.required_input_names()) - static_inputs)


def node_condition_values(
    graph: networkx.DiGraph, source_id: NodeIdType
) -> Dict[str, set]:
    condition_values = defaultdict(set)
    for target_id in node_successors(graph, source_id, link_has_conditions=True):
        for condition in graph[source_id][target_id]["conditions"]:
            varname = condition["source_output"]
            value = condition["value"]
            condition_values[varname].add(value)
    return condition_values


def node_has_noncovered_conditions(
    graph: networkx.DiGraph, source_id: NodeIdType
) -> bool:
    conditions_else_value = graph.nodes[source_id].get("conditions_else_value", None)
    complements = {
        True: {False, conditions_else_value},
        False: {True, conditions_else_value},
    }
    condition_values = node_condition_values(graph, source_id)
    for values in condition_values.values():
        for value in values:
            cvalue = complements.get(value, conditions_else_value)
            if cvalue not in values:
                return True
    return False


def node_is_start_node(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    node = graph.nodes[node_id]
    if node.get("force_start_node", False):
        return True

    return not node_has_predecessors(graph, node_id)


def start_nodes(graph: networkx.DiGraph) -> Set[NodeIdType]:
    """Nodes from which the graph execution starts"""

    start_nodes: Set[NodeIdType] = set(
        node_id for node_id in graph.nodes if node_is_start_node(graph, node_id)
    )
    if start_nodes:
        return start_nodes

    return set(
        node_id
        for node_id in graph.nodes
        if has_required_static_inputs(graph, node_id)
        and not has_required_predecessors(graph, node_id)
    )


def end_nodes(graph: networkx.DiGraph) -> Set[NodeIdType]:
    """Nodes at which an graph execution thread may end and
    which result need to be recorded.
    """
    nodes = set(
        node_id for node_id in graph.nodes if node_is_pure_end_node(graph, node_id)
    )
    if nodes:
        return nodes
    return set(node_id for node_id in graph.nodes if node_is_end_node(graph, node_id))


def node_is_pure_end_node(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    """Node without successors or only error handlers"""
    return not node_has_successors(graph, node_id, link_has_on_error=False)


def node_is_end_node(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    """A pure end node or a node with uncovered conditions"""
    if node_is_pure_end_node(graph, node_id):
        return True
    if node_has_noncovered_conditions(graph, node_id):
        return True
    return False


def topological_sort(graph: networkx.DiGraph) -> Iterator[NodeIdType]:
    """Sort node names for sequential instantiation+execution of DAGs"""
    if graph_is_cyclic(graph):
        raise RuntimeError("Sorting nodes is not possible for cyclic graphs")
    yield from networkx.topological_sort(graph)


def node_pure_descendants(
    graph: networkx.DiGraph, node_id: NodeIdType, include_node: bool = False
) -> Iterator[NodeIdType]:
    """Yields all descendants which do not depend on anything else than `node_id`"""
    if include_node:
        yield node_id
    nodes = {node_id}
    iter_successors = {node_id}
    while iter_successors:
        new_iter_successors = set()
        for node_id in iter_successors:
            for target_id in graph.successors(node_id):
                if target_id in nodes:
                    continue  # loopback
                predecessors = set(graph.predecessors(target_id))
                if predecessors - nodes:
                    continue  # depends on a node outside the branch
                yield target_id
                new_iter_successors.add(target_id)
        iter_successors = new_iter_successors
