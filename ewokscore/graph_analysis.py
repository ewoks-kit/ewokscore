from typing import Mapping, Iterable
import networkx

from .utils import dict_merge
from .node import NodeIdType


def flatten_multigraph(graph: networkx.DiGraph) -> networkx.DiGraph:
    """The attributes of links between the same two nodes are merged."""
    if not graph.is_multigraph():
        return graph
    newgraph = networkx.DiGraph(**graph.graph)

    edgeattrs = dict()
    for edge, attrs in graph.edges.items():
        key = edge[:2]
        mergedattrs = edgeattrs.setdefault(key, dict())
        # mergedattrs["links"] and attrs["links"]
        # could be two sequences that need to be concatenated
        dict_merge(mergedattrs, attrs, contatenate_sequences=True)

    for name, attrs in graph.nodes.items():
        newgraph.add_node(name, **attrs)
    for (source_id, target_id), mergedattrs in edgeattrs.items():
        newgraph.add_edge(source_id, target_id, **mergedattrs)
    return newgraph


def pure_descendants(
    graph: networkx.DiGraph, node_id: NodeIdType, include_node: bool = False
) -> Iterable[NodeIdType]:
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
                    continue
                predecessors = set(graph.predecessors(target_id))
                if predecessors - nodes:
                    continue
                yield target_id
                new_iter_successors.add(target_id)
        iter_successors = new_iter_successors


def connect_default_error_handlers(graph: networkx.DiGraph) -> networkx.DiGraph:
    """All nodes without an error handler will be connected to all default error handlers.
    Default error handlers without predecessors will be removed.
    """
    error_handlers = dict()
    for node_id, attrs in graph.nodes.items():
        link_attrs = attrs.pop("default_error_node", None)
        if link_attrs is None:
            continue
        if not isinstance(link_attrs, Mapping):
            link_attrs = dict()
        link_attrs["on_error"] = True
        if not (set(link_attrs.keys()) & {"map_all_data", "data_mapping"}):
            link_attrs["map_all_data"] = True
        error_handlers[node_id] = link_attrs

    nodes_without_error_handlers = set(graph.nodes.keys()) - set(error_handlers)
    for edge, attrs in graph.edges.items():
        source_id = edge[0]
        if attrs.get("on_error"):
            if source_id in nodes_without_error_handlers:
                nodes_without_error_handlers.remove(source_id)
    if nodes_without_error_handlers:
        for source_id in nodes_without_error_handlers:
            for target_id, link_attrs in error_handlers.items():
                graph.add_edge(source_id, target_id, **link_attrs)
    else:
        for node_id in error_handlers:
            try:
                next(graph.predecessors())
            except StopIteration:
                nodes = set(pure_descendants(graph, node_id, include_node=True))
                graph.remove_nodes_from(nodes)
