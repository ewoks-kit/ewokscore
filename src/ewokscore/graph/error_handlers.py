from typing import Dict
from typing import Mapping

import networkx

from ..node import NodeIdType
from ._analysis import GraphAnalysis


def connect_default_error_handlers(graph: networkx.DiGraph) -> None:
    """All nodes without an error handler will be connected to all default error handlers.
    Default error handlers without predecessors will be removed.
    """
    default_error_handlers = _pop_default_error_handlers(graph)
    if not default_error_handlers:
        return

    graph_analysis = GraphAnalysis(graph)

    # All nodes which are not default error handlers and do not have an error handler yet
    nodes_without_error_handlers = {
        node_id
        for node_id in graph.nodes
        if node_id not in default_error_handlers
        and not graph_analysis.node_has_error_handlers(node_id)
    }

    # Remove nodes that have any of the default error handlers as ancestor
    for node_id in default_error_handlers:
        nodes_without_error_handlers -= graph_analysis.descendants(node_id)

    if nodes_without_error_handlers:
        # Connect to the default error handlers
        for source_id in nodes_without_error_handlers:
            for target_id, link_attrs in default_error_handlers.items():
                if not graph.has_edge(source_id, target_id):
                    graph.add_edge(source_id, target_id, **link_attrs)
    else:
        # Remove the default error handlers that nothing can trigger, together
        # with the nodes that depend on nothing else. Collect them all before
        # touching the graph, since that invalidates `graph_analysis`.
        nodes_to_remove = set()
        for node_id in default_error_handlers:
            if graph_analysis.node_has_predecessors(node_id):
                continue
            # Default error handler has no predecessors
            nodes_to_remove.update(
                graph_analysis.node_pure_descendants(node_id, include_node=True)
            )
        graph.remove_nodes_from(nodes_to_remove)


def _pop_default_error_handlers(graph: networkx.DiGraph) -> Dict[NodeIdType, dict]:
    """Extract the default error handler nodes and the attributes of the error
    handler links to be created for them.
    """
    default_error_handlers: Dict[NodeIdType, dict] = dict()
    for node_id, attrs in graph.nodes.items():
        default_error_node = attrs.pop("default_error_node", False)
        if not default_error_node:
            continue

        link_attrs = attrs.pop("default_error_attributes", None)
        if not isinstance(link_attrs, Mapping):
            link_attrs = dict()
        else:
            link_attrs = dict(link_attrs)

        link_attrs["on_error"] = True
        if not (set(link_attrs.keys()) & {"map_all_data", "data_mapping"}):
            link_attrs["map_all_data"] = True

        default_error_handlers[node_id] = link_attrs
    return default_error_handlers
