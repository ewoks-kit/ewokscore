import itertools
from typing import Optional, Tuple, Union, Any
import networkx
from .utils import dict_merge
from .node import flatten_node_id


NodeIdType = Union[str, Tuple[str, Any]]  # Any is NodeIdType


def _append_subnode_id(node_id: NodeIdType, sub_node_id: str) -> NodeIdType:
    if isinstance(node_id, tuple):
        parent, child = node_id
        return parent, _append_subnode_id(child, sub_node_id)
    else:
        return node_id, sub_node_id


def _get_subgraph(node_id: NodeIdType, subgraphs: dict):
    if isinstance(node_id, str):
        return subgraphs.get(node_id)
    subgraph_id, subnode_id = node_id
    try:
        subgraph = subgraphs[subgraph_id]
    except KeyError:
        raise ValueError(node_id, f"{repr(subgraph_id)} is not a subgraph")
    flat_subnode_id = flatten_node_id(subnode_id)
    n = len(flat_subnode_id)
    for node_id in subgraph.graph.nodes:
        flat_node_id = flatten_node_id(node_id)
        nflatid = len(flat_node_id)
        if flat_node_id == flat_subnode_id:
            return None  # a task node
        if nflatid > n and flat_node_id[:n] == flat_subnode_id:
            return subgraph  # a graph node
    raise ValueError(
        f"{subnode_id} is not a node or subgraph of subgraph {repr(subgraph_id)}",
    )


def _resolve_node_alias(
    node_id: NodeIdType, graph_attrs: dict, input_nodes: bool
) -> Tuple[NodeIdType, dict]:
    link_attrs = dict()
    if input_nodes:
        aliases = graph_attrs.get("input_nodes", None)
    else:
        aliases = graph_attrs.get("output_nodes", None)
    if not aliases:
        return node_id, link_attrs
    alias_attrs = None
    for alias_attrsi in aliases:
        if alias_attrsi["id"] == node_id:
            alias_attrs = alias_attrsi
            break
    if not alias_attrs:
        return node_id, link_attrs
    sub_node = alias_attrs.get("sub_node", None)
    if sub_node:
        sub_node_id = alias_attrs["node"], sub_node
    else:
        sub_node_id = alias_attrs["node"]
    link_attrs = alias_attrs.get("link_attributes", link_attrs)
    return sub_node_id, link_attrs


def _get_subnode_id(
    node_id: NodeIdType, sub_graph_nodes: dict, subgraphs: dict, source: bool
) -> Tuple[NodeIdType, Optional[dict]]:
    if source:
        key = "sub_source"
    else:
        key = "sub_target"

    subgraph = _get_subgraph(node_id, subgraphs)
    if subgraph is None:
        if key in sub_graph_nodes:
            raise ValueError(
                f"'{node_id}' is not a graph so 'sub_source' should not be specified"
            )
        return node_id, None

    try:
        sub_node_id = sub_graph_nodes[key]
    except KeyError:
        raise ValueError(
            f"The '{key}' attribute to specify a node in subgraph '{node_id}' is missing"
        ) from None
    sub_node_id, link_attrs = _resolve_node_alias(
        sub_node_id, subgraph.graph.graph, input_nodes=not source
    )
    new_node_id = _append_subnode_id(node_id, sub_node_id)
    return new_node_id, link_attrs


def _get_subnode_info(
    source_id: NodeIdType,
    target_id: NodeIdType,
    sub_graph_nodes: dict,
    subgraphs: dict,
) -> Tuple[NodeIdType, NodeIdType, dict, bool]:
    sub_source, source_link_attrs = _get_subnode_id(
        source_id, sub_graph_nodes, subgraphs, source=True
    )
    sub_target, target_link_attrs = _get_subnode_id(
        target_id, sub_graph_nodes, subgraphs, source=False
    )
    if source_link_attrs:
        link_attrs = source_link_attrs
    else:
        link_attrs = dict()
    if target_link_attrs:
        link_attrs.update(target_link_attrs)
    target_is_graph = target_link_attrs is not None
    return sub_source, sub_target, link_attrs, target_is_graph


def _replace_aliases(
    graph: networkx.DiGraph, subgraphs: dict, input_nodes: bool
) -> dict:
    if input_nodes:
        aliases = graph.graph.get("input_nodes")
        if not aliases:
            return
        source = False
        key = "sub_target"
    else:
        aliases = graph.graph.get("output_nodes")
        if not aliases:
            return
        source = True
        key = "sub_source"

    for alias_attrs in aliases:
        node_id = alias_attrs["node"]
        sub_node = alias_attrs.pop("sub_node", None)
        if sub_node:
            node_id = node_id, sub_node
        link_attrs = None
        if isinstance(node_id, tuple):
            parent, child = node_id
            node_id, link_attrs = _get_subnode_id(
                parent, {key: child}, subgraphs=subgraphs, source=source
            )
        if link_attrs:
            link_attrs.update(alias_attrs.get("link_attributes", dict()))
            alias_attrs["link_attributes"] = link_attrs
        alias_attrs["node"] = node_id


def extract_graph_nodes(graph: networkx.DiGraph, subgraphs) -> Tuple[list, dict]:
    """Removes all graph nodes from `graph` and returns a list of edges
    between the nodes from `graph` and `subgraphs`.

    Nodes in sub-graphs are defines in the `sub_graph_nodes` link attribute.
    For example:

        link_attrs = {
            "source": "subgraph1",
            "target": "subgraph2",
            "data_mapping": [{"target_input": 0, "source_output":"return_value"}],
            "sub_graph_nodes": {
                "sub_source": ("subsubgraph", ("subsubsubgraph", "task2")),
                "sub_target": "task1",
            },
        }
    """
    edges = list()
    update_attrs = dict()
    graph_is_multi = graph.is_multigraph()
    for subgraph_id in subgraphs:
        it1 = (
            (source_id, subgraph_id) for source_id in graph.predecessors(subgraph_id)
        )
        it2 = ((subgraph_id, target_id) for target_id in graph.successors(subgraph_id))
        for source_id, target_id in itertools.chain(it1, it2):
            all_link_attrs = graph[source_id][target_id]
            if graph_is_multi:
                all_link_attrs = all_link_attrs.values()
            else:
                all_link_attrs = [all_link_attrs]
            for link_attrs in all_link_attrs:
                sub_graph_nodes = {
                    key: link_attrs.pop(key)
                    for key in ["sub_source", "sub_target", "sub_target_attributes"]
                    if key in link_attrs
                }
                if not sub_graph_nodes:
                    continue
                source, target, default_link_attrs, target_is_graph = _get_subnode_info(
                    source_id, target_id, sub_graph_nodes, subgraphs
                )
                if default_link_attrs:
                    link_attrs = {**default_link_attrs, **link_attrs}
                sub_target_attributes = sub_graph_nodes.get(
                    "sub_target_attributes", None
                )
                if sub_target_attributes:
                    if not target_is_graph:
                        raise ValueError(
                            f"'{target_id}' is not a graph so 'sub_target_attributes' should not be specified"
                        )
                    update_attrs[target] = sub_target_attributes
                edges.append((source, target, link_attrs))

    _replace_aliases(graph, subgraphs, input_nodes=True)
    _replace_aliases(graph, subgraphs, input_nodes=False)
    graph.remove_nodes_from(subgraphs.keys())
    return edges, update_attrs


def add_subgraph_links(graph: networkx.DiGraph, edges: list, update_attrs: dict):
    # Output from extract_graph_nodes
    for source, target, _ in edges:
        if source not in graph.nodes:
            raise ValueError(
                f"Source node {repr(source)} of link |{repr(source)} -> {repr(target)}| does not exist"
            )
        if target not in graph.nodes:
            raise ValueError(
                f"Target node {repr(target)} of link |{repr(source)} -> {repr(target)}| does not exist"
            )
    graph.add_edges_from(edges)  # This adds missing nodes
    for node, attrs in update_attrs.items():
        node_attrs = graph.nodes[node]
        if attrs:
            dict_merge(node_attrs, attrs, overwrite=True)
