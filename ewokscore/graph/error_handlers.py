from typing import Mapping
import networkx

from .analysis import node_pure_descendants
from ewokscore.graph import analysis


def connect_default_error_handlers(graph: networkx.DiGraph) -> networkx.DiGraph:
    """All nodes without an error handler will be connected to all default error handlers.
    Default error handlers without predecessors will be removed.
    """
    default_error_handlers = dict()
    for node_id, attrs in graph.nodes.items():
        default_error_node = attrs.pop("default_error_node", False)
        if not default_error_node:
            continue
        link_attrs = attrs.pop("default_error_attributes", None)
        if not isinstance(link_attrs, Mapping):
            link_attrs = dict()
        link_attrs["on_error"] = True
        if not (set(link_attrs.keys()) & {"map_all_data", "data_mapping"}):
            link_attrs["map_all_data"] = True
        default_error_handlers[node_id] = link_attrs

    # All nodes which are not default error handlers
    nodes_without_error_handlers = set(graph.nodes.keys()) - set(default_error_handlers)

    # Remove the nodes that already have an error handler
    for edge, attrs in graph.edges.items():
        source_id = edge[0]
        if attrs.get("on_error"):
            if source_id in nodes_without_error_handlers:
                nodes_without_error_handlers.remove(source_id)

    # Remove nodes that have any of the default error handlers as ancestor
    for node_id in set(nodes_without_error_handlers):
        for ancestor_id in analysis.node_ancestors(graph, node_id):
            if ancestor_id in default_error_handlers:
                nodes_without_error_handlers.remove(node_id)
                break

    if nodes_without_error_handlers:
        # Connect to the default error handlers
        for source_id in nodes_without_error_handlers:
            for target_id, link_attrs in default_error_handlers.items():
                graph.add_edge(source_id, target_id, **link_attrs)
    else:
        # Remove the default error handlers and their pure descendants
        for node_id in default_error_handlers:
            try:
                next(graph.predecessors())
            except StopIteration:
                nodes = set(node_pure_descendants(graph, node_id, include_node=True))
                graph.remove_nodes_from(nodes)
