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
        parent, child = node_name
        return parent, _append_subnode_name(child, sub_node_name)
    else:
        return node_name, sub_node_name


def _get_subgraph(node_name: NodeIdType, subgraphs: dict):
    if isinstance(node_name, str):
        return subgraphs.get(node_name)

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
            return None  # a task node
        if nname > n and flat_name[:n] == flat_subnode_name:
            return subgraph  # a graph node
    raise ValueError(
        f"{subnode_name} is not a node or subgraph of subgraph {repr(subgraph_name)}",
    )


def _pop_subgraph_node_names_deprecated(
    source_name, target_name, link_attrs, subgraphs
):
    if _get_subgraph(source_name, subgraphs):
        source = _pop_subgraph_node_name_deprecated(
            source_name, link_attrs, source=True
        )
    else:
        link_attrs.pop("source", None)
        source = source_name

    if _get_subgraph(target_name, subgraphs):
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


def _resolve_node_alias(
    node_name: NodeIdType, graph_attrs: dict, input_nodes: bool
) -> NodeIdType:
    if input_nodes:
        aliases = graph_attrs.get("input_nodes", None)
    else:
        aliases = graph_attrs.get("output_nodes", None)
    if not aliases:
        return node_name
    node_info = None
    for alias_attrs in aliases:
        if alias_attrs["alias"] == node_name:
            node_info = alias_attrs
            break
    if not node_info:
        return node_name
    sub_node = node_info.get("sub_node", None)
    if sub_node:
        return node_info["id"], sub_node
    else:
        return node_info["id"]


def _get_subnode_name(
    node_name: NodeIdType, sub_graph_nodes: dict, subgraphs: dict, source: bool
) -> Tuple[NodeIdType, bool]:
    if source:
        key = "sub_source"
    else:
        key = "sub_target"

    subgraph = _get_subgraph(node_name, subgraphs)
    if subgraph is None:
        if key in sub_graph_nodes:
            raise ValueError(
                f"'{node_name}' is not a graph so 'sub_source' should not be specified"
            )
        return node_name, False

    try:
        sub_node_name = sub_graph_nodes[key]
    except KeyError:
        raise ValueError(
            f"The '{key}' attribute to specify a node in subgraph '{node_name}' is missing"
        ) from None
    sub_node_name = _resolve_node_alias(
        sub_node_name, subgraph.graph.graph, input_nodes=not source
    )
    new_node_name = _append_subnode_name(node_name, sub_node_name)
    return new_node_name, True


def _get_subnode_info(
    source_name: NodeIdType,
    target_name: NodeIdType,
    sub_graph_nodes: dict,
    subgraphs: dict,
) -> Tuple[NodeIdType, NodeIdType, bool]:
    sub_source, _ = _get_subnode_name(
        source_name, sub_graph_nodes, subgraphs, source=True
    )
    sub_target, target_is_graph = _get_subnode_name(
        target_name, sub_graph_nodes, subgraphs, source=False
    )
    return sub_source, sub_target, target_is_graph


def _get_nested_subnode_info(
    source_name: NodeIdType,
    target_name: NodeIdType,
    sub_graph_nodes: dict,
    subgraphs: dict,
) -> Tuple[NodeIdType, NodeIdType, bool]:
    sub_source, sub_target, target_is_graph = _get_subnode_info(
        source_name, target_name, sub_graph_nodes, subgraphs
    )
    sub_graph_nodes = sub_graph_nodes.pop("sub_graph_nodes", None)
    while sub_graph_nodes:
        warnings.warn("nested 'sub_graph_nodes' is deprecated", FutureWarning)
        sub_source, sub_target, _ = _get_subnode_info(
            sub_source, sub_target, sub_graph_nodes, subgraphs
        )
        sub_graph_nodes = sub_graph_nodes.pop("sub_graph_nodes", None)
    return sub_source, sub_target, target_is_graph


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
        node_name = alias_attrs["id"]
        sub_node = alias_attrs.pop("sub_node", None)
        if sub_node:
            node_name = node_name, sub_node
        if isinstance(node_name, tuple):
            parent, child = node_name
            node_name, _ = _get_subnode_name(
                parent, {key: child}, subgraphs=subgraphs, source=source
            )
        alias_attrs["id"] = node_name


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
                    source, target, target_is_graph = _get_nested_subnode_info(
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
