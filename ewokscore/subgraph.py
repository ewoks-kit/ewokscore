import itertools
from typing import Tuple, Union, Any
import warnings
import networkx
from .utils import dict_merge
from .node import flatten_node_name


NodeIdType = Union[str, Tuple[str, Any]]  # Any is NodeIdType


def _pop_subgraph_node_name_deprecated(subgraph_name, link_attrs, source=True):
    if source:
        key = "source"
    else:
        key = "target"
    try:
        subgraph_node_name = link_attrs.pop(key)
    except KeyError:
        raise ValueError(
            f"The '{key}' attribute to specify a node in subgraph '{subgraph_name}' is missing"
        ) from None

    return _append_subnode_name(subgraph_name, subgraph_node_name)


def _append_subnode_name(node_name: NodeIdType, sub_node_name: str) -> NodeIdType:
    if isinstance(node_name, tuple):
        assert len(node_name) == 2, node_name
        parent, child = node_name
        return parent, _append_subnode_name(child, sub_node_name)
    else:
        return node_name, sub_node_name


def _is_subgraph(node_name: NodeIdType, subgraphs: dict) -> bool:
    if isinstance(node_name, str):
        return node_name in subgraphs

    subgraph_name, subnode_name = node_name
    try:
        subgraph = subgraphs[subgraph_name]
    except KeyError:
        raise ValueError(node_name, f"{repr(subgraph_name)} is not a subgraph")
    flat_subnode_name = flatten_node_name(subnode_name)
    n = len(flat_subnode_name)
    for name in subgraph.graph.nodes:
        flat_name = flatten_node_name(name)
        nname = len(flat_name)
        if flat_name == flat_subnode_name:
            return False  # a task node
        if nname > n and flat_name[:n] == flat_subnode_name:
            return True  # a graph node
    raise ValueError(
        f"{subnode_name} is not a node or subgraph of subgraph {repr(subgraph_name)}",
    )


def _pop_subgraph_node_names_deprecated(
    source_name, target_name, link_attrs, subgraphs
):
    if _is_subgraph(source_name, subgraphs):
        source = _pop_subgraph_node_name_deprecated(
            source_name, link_attrs, source=True
        )
    else:
        link_attrs.pop("source", None)
        source = source_name

    if _is_subgraph(target_name, subgraphs):
        target = _pop_subgraph_node_name_deprecated(
            target_name, link_attrs, source=False
        )
        target_attributes = link_attrs.pop("node_attributes", None)
    else:
        link_attrs.pop("target", None)
        target = target_name
        link_attrs.pop("node_attributes", None)
        target_attributes = None

    return source, target, target_attributes


def _extract_subgraph_links_deprecated(source_name, target_name, links, subgraphs):
    for link_attrs in links:
        link_attrs = dict(link_attrs)
        source, target, target_attributes = _pop_subgraph_node_names_deprecated(
            source_name, target_name, link_attrs, subgraphs
        )
        sublinks = link_attrs.pop("links", None)
        if sublinks:
            yield from _extract_subgraph_links_deprecated(
                source, target, sublinks, subgraphs
            )
        else:
            yield source, target, link_attrs, target_attributes


def _get_subnode_name(
    node_name: NodeIdType, sub_graph_nodes: dict, source: bool = True
) -> NodeIdType:
    if source:
        key = "sub_source"
    else:
        key = "sub_target"
    try:
        sub_node_name = sub_graph_nodes[key]
    except KeyError:
        raise ValueError(
            f"The '{key}' attribute to specify a node in subgraph '{node_name}' is missing"
        ) from None

    return _append_subnode_name(node_name, sub_node_name)


def _get_subnode_info(
    source_name: NodeIdType,
    target_name: NodeIdType,
    sub_graph_nodes: dict,
    subgraphs: dict,
) -> Tuple[NodeIdType, NodeIdType, bool]:
    if _is_subgraph(source_name, subgraphs):
        sub_source = _get_subnode_name(source_name, sub_graph_nodes, source=True)
    else:
        if "sub_source" in sub_graph_nodes:
            raise ValueError(
                f"'{source_name}' is not a graph so 'sub_source' should not be specified"
            )
        sub_source = source_name

    if _is_subgraph(target_name, subgraphs):
        sub_target = _get_subnode_name(target_name, sub_graph_nodes, source=False)
        target_is_graph = True
    else:
        if "sub_target" in sub_graph_nodes:
            raise ValueError(
                f"'{target_name}' is not a graph so 'sub_target' should not be specified"
            )
        sub_target = target_name
        target_is_graph = True

    return sub_source, sub_target, target_is_graph


def _get_subnodes_info(
    source_name: NodeIdType,
    target_name: NodeIdType,
    sub_graph_nodes: dict,
    subgraphs: dict,
) -> Tuple[NodeIdType, NodeIdType, bool]:
    """The `sub_graph_nodes` dictionary is a nested dictionary, for example"""

    sub_source, sub_target, target_is_graph = _get_subnode_info(
        source_name, target_name, sub_graph_nodes, subgraphs
    )
    sub_graph_nodes = sub_graph_nodes.pop("sub_graph_nodes", None)
    while sub_graph_nodes:
        sub_source, sub_target, _ = _get_subnode_info(
            sub_source, sub_target, sub_graph_nodes, subgraphs
        )
        sub_graph_nodes = sub_graph_nodes.pop("sub_graph_nodes", None)
    return sub_source, sub_target, target_is_graph


def extract_graph_nodes(graph: networkx.DiGraph, subgraphs) -> Tuple[list, dict]:
    """Removes all graph nodes from `graph` and returns a list of edges
    between the nodes from `graph` and `subgraphs`.

    Nodes in sub-graphs are defines in the `sub_graph_nodes` link attribute.
    For example:

        link_attrs = {
            "source": "subgraph1",
            "target": "subgraph2",
            "arguments": {0: "return_value"},
            "sub_graph_nodes": {
                "sub_source": "subsubgraph",
                "sub_target": "task1",
                "sub_graph_nodes": {
                    "sub_source": "subsubsubgraph",
                    "sub_graph_nodes": {"sub_source": "task2"},
                },
            },
        }
    """
    edges = list()
    update_attrs = dict()
    graph_is_multi = graph.is_multigraph()
    for subgraph_name in subgraphs:
        it1 = (
            (source_name, subgraph_name)
            for source_name in graph.predecessors(subgraph_name)
        )
        it2 = (
            (subgraph_name, target_name)
            for target_name in graph.successors(subgraph_name)
        )
        for source_name, target_name in itertools.chain(it1, it2):
            all_link_attrs = graph[source_name][target_name]
            if graph_is_multi:
                all_link_attrs = all_link_attrs.values()
            else:
                all_link_attrs = [all_link_attrs]
            for link_attrs in all_link_attrs:
                links = link_attrs.pop("links", None)
                sub_graph_nodes = link_attrs.pop("sub_graph_nodes", None)
                if not links and not sub_graph_nodes:
                    continue
                if links and sub_graph_nodes:
                    raise ValueError(
                        "cannot use link attributes 'links' and 'sub_graph_nodes' at the same time. 'links' is a deprecated link attribute."
                    )
                if links:
                    warnings.warn(
                        "'links' is a deprecated link attribute. Use 'sub_graph_nodes' instead (link attributes need to be moved up)."
                    )
                    itlinks = _extract_subgraph_links_deprecated(
                        source_name, target_name, links, subgraphs
                    )
                    for source, target, link_attrs, target_attributes in itlinks:
                        if target_attributes:
                            update_attrs[target] = target_attributes
                        edges.append((source, target, link_attrs))
                else:
                    source, target, target_is_graph = _get_subnodes_info(
                        source_name, target_name, sub_graph_nodes, subgraphs
                    )
                    sub_target_attributes = link_attrs.pop(
                        "sub_target_attributes", None
                    )
                    if sub_target_attributes:
                        if not target_is_graph:
                            raise ValueError(
                                f"'{target_name}' is not a graph so 'sub_target_attributes' should not be specified"
                            )
                        update_attrs[target] = sub_target_attributes
                    edges.append((source, target, link_attrs))

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
