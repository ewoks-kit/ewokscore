from typing import Optional

import networkx

from ..inittask import validate_task_executable
from ..node import NodeIdType
from ._analysis import GraphAnalysis
from .schema import update_to_latest_schema


def validate_graph(
    graph: networkx.DiGraph, graph_analysis: Optional[GraphAnalysis] = None
) -> None:
    update_to_latest_schema(graph)
    _validate_nodes(graph, graph_analysis)
    _validate_links(graph)


def _validate_nodes(
    graph: networkx.DiGraph, graph_analysis: Optional[GraphAnalysis]
) -> None:
    for node_id, node_attrs in graph.nodes.items():
        validate_task_executable(node_id, node_attrs)

        # Avoid the graph analysis when the links cannot be invalid
        if not _may_have_invalid_input_links(graph, node_id):
            continue
        if graph_analysis is None:
            graph_analysis = GraphAnalysis(graph)

        inputs_from_required = dict()
        for source_id in graph_analysis.required_predecessors(node_id):
            link_attrs = graph[source_id][node_id]
            arguments = link_attrs.get("data_mapping", list())
            for arg in arguments:
                try:
                    name = arg["target_input"]
                except KeyError:
                    raise KeyError(
                        f"Argument '{arg}' of link '{source_id}' -> '{node_id}' is missing a 'target_input' key"
                    ) from None
                other_source_id = inputs_from_required.get(name)
                if other_source_id:
                    raise ValueError(
                        f"Node {repr(source_id)} and {repr(other_source_id)} both connect to the input {repr(name)} of {repr(node_id)}"
                    )
                inputs_from_required[name] = source_id


def _may_have_invalid_input_links(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    """Whether an input of the node is connected more than once or a link has
    an argument without `target_input`.
    """
    names = set()
    for link_attrs in graph.pred[node_id].values():
        for arg in link_attrs.get("data_mapping", list()):
            name = arg.get("target_input")
            if name is None or name in names:
                return True
            names.add(name)
    return False


def _validate_links(graph: networkx.DiGraph) -> None:
    for (source, target), linkattrs in graph.edges.items():
        err_msg = f"Link {source}->{target}: '{{}}' and '{{}}' cannot be used together"
        if linkattrs.get("map_all_data") and linkattrs.get("data_mapping"):
            raise ValueError(err_msg.format("map_all_data", "data_mapping"))
        if linkattrs.get("on_error") and linkattrs.get("conditions"):
            raise ValueError(err_msg.format("on_error", "conditions"))
