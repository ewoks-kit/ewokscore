import itertools
from typing import Iterable, Optional, Tuple, Union, Any
import networkx
from copy import deepcopy

from ..utils import dict_merge
from ..node import flatten_node_id


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


def _alias_to_node_id(alias_attrs: dict) -> NodeIdType:
    sub_node = alias_attrs.get("sub_node", None)
    if sub_node:
        return alias_attrs["node"], sub_node
    else:
        return alias_attrs["node"]


def _resolve_node_aliases(
    node_id: NodeIdType, graph_attrs: dict, input_nodes: bool
) -> Iterable[Tuple[NodeIdType, dict]]:
    if input_nodes:
        aliases = graph_attrs.get("input_nodes", list())
    else:
        aliases = graph_attrs.get("output_nodes", list())
    aliases = [alias_attrs for alias_attrs in aliases if alias_attrs["id"] == node_id]
    if aliases:
        for alias_attrs in aliases:
            sub_node_id = _alias_to_node_id(alias_attrs)
            link_attributes = alias_attrs.get("link_attributes", dict())
            yield sub_node_id, link_attributes
    else:
        yield node_id, dict()


def _resolve_all_node_aliases(
    graph_attrs: dict, input_nodes: bool
) -> Iterable[NodeIdType]:
    if input_nodes:
        aliases = graph_attrs.get("input_nodes", list())
    else:
        aliases = graph_attrs.get("output_nodes", list())
    for alias_attrs in aliases:
        yield _alias_to_node_id(alias_attrs)


def _get_subnode_ids(
    node_id: NodeIdType, link_attrs_subgraph_keys: dict, subgraphs: dict, source: bool
) -> Iterable[Tuple[NodeIdType, Optional[dict]]]:
    if source:
        key = "sub_source"
    else:
        key = "sub_target"
    subgraph = _get_subgraph(node_id, subgraphs)
    if subgraph is None:
        # node_id is not a subgraph
        if key in link_attrs_subgraph_keys:
            raise ValueError(
                f"'{node_id}' is not a graph so 'sub_source' should not be specified"
            )
        yield node_id, None
    else:
        # node_id is a subgraph
        try:
            sub_node_id = link_attrs_subgraph_keys[key]
        except KeyError:
            raise ValueError(
                f"the '{key}' attribute to specify a node in subgraph '{node_id}' is missing"
            ) from None
        for sub_node_id, link_attributes in _resolve_node_aliases(
            sub_node_id, subgraph.graph.graph, input_nodes=not source
        ):
            new_node_id = _append_subnode_id(node_id, sub_node_id)
            yield new_node_id, link_attributes


def _get_subnode_attributes(
    node_id: NodeIdType, subgraphs: dict, graph_node_attrs: dict
) -> Iterable[Tuple[NodeIdType, dict]]:
    """Update all input node attributes of the subgraph with the graph node attributes from the super graph"""
    transfer_attributes = {
        "default_inputs",
        "inputs_complete",
        "conditions_else_value",
        "default_error_node",
    }
    node_attrs = {k: v for k, v in graph_node_attrs.items() if k in transfer_attributes}
    if not node_attrs:
        return
    subgraph = _get_subgraph(node_id, subgraphs)
    if subgraph is None:
        # node_id is not a subgraph
        return
    # node_id is a subgraph
    for sub_node_id in _resolve_all_node_aliases(
        subgraph.graph.graph, input_nodes=True
    ):
        new_node_id = _append_subnode_id(node_id, sub_node_id)
        yield new_node_id, node_attrs


def _get_subnode_links(
    source_id: NodeIdType,
    target_id: NodeIdType,
    link_attrs_subgraph_keys: dict,
    subgraphs: dict,
) -> Iterable[Tuple[NodeIdType, NodeIdType, dict, bool]]:
    sources = list(
        _get_subnode_ids(source_id, link_attrs_subgraph_keys, subgraphs, source=True)
    )
    targets = list(
        _get_subnode_ids(target_id, link_attrs_subgraph_keys, subgraphs, source=False)
    )
    for sub_source, source_link_attrs in sources:
        for sub_target, target_link_attrs in targets:
            if source_link_attrs:
                link_attrs = source_link_attrs
            else:
                link_attrs = dict()
            if target_link_attrs:
                link_attrs.update(target_link_attrs)
            target_is_graph = target_link_attrs is not None
            yield sub_source, sub_target, link_attrs, target_is_graph


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

    new_aliases = list()
    for alias_attrs in aliases:
        node_id = alias_attrs["node"]
        sub_node = alias_attrs.pop("sub_node", None)
        if sub_node:
            node_id = node_id, sub_node
        if not isinstance(node_id, tuple):
            new_aliases.append(alias_attrs)
            continue
        parent, child = node_id
        original_alias_attrs = alias_attrs
        for node_id, link_attrs in _get_subnode_ids(
            parent, {key: child}, subgraphs=subgraphs, source=source
        ):
            alias_attrs = deepcopy(original_alias_attrs)
            if link_attrs:
                link_attrs.update(alias_attrs.get("link_attributes", dict()))
                alias_attrs["link_attributes"] = link_attrs
            alias_attrs["node"] = node_id
            new_aliases.append(alias_attrs)

    if input_nodes:
        graph.graph["input_nodes"] = new_aliases
    else:
        graph.graph["output_nodes"] = new_aliases


def extract_graph_nodes(graph: networkx.DiGraph, subgraphs) -> Tuple[list, dict]:
    """Removes all graph nodes from `graph` and returns a list of edges
    between the nodes from `graph` and `subgraphs`.

    Nodes in sub-graphs are defines in the `link_attrs_subgraph_keys` link attribute.
    For example:

    .. code: python

        link_attrs = {
            "source": "subgraph1",
            "target": "subgraph2",
            "data_mapping": [{"source_output":"return_value", "target_input": 0}],
            "link_attrs_subgraph_keys": {
                "sub_source": ("subsubgraph", ("subsubsubgraph", "task2")),
                "sub_target": "task1",
            },
        }
    """
    edges = list()
    update_attrs = dict()
    graph_is_multi = graph.is_multigraph()
    for subgraph_id in subgraphs:
        # Nodes to be updated after flattening the graph
        for node_id, graph_node_attrs in _get_subnode_attributes(
            subgraph_id, subgraphs, graph.nodes[subgraph_id]
        ):
            if node_id in update_attrs:
                update_attrs[node_id].update(graph_node_attrs)
            else:
                update_attrs[node_id] = graph_node_attrs
        # Links to be made after flattening the graph
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
                link_attrs_subgraph_keys = {
                    key: link_attrs.pop(key)
                    for key in ["sub_source", "sub_target", "sub_target_attributes"]
                    if key in link_attrs
                }
                if not link_attrs_subgraph_keys:
                    continue
                original_link_attrs = link_attrs
                links = _get_subnode_links(
                    source_id, target_id, link_attrs_subgraph_keys, subgraphs
                )
                for (source, target, default_link_attrs, target_is_graph) in links:
                    link_attrs = deepcopy(original_link_attrs)
                    if default_link_attrs:
                        link_attrs = {**default_link_attrs, **link_attrs}
                    sub_target_attributes = link_attrs_subgraph_keys.get(
                        "sub_target_attributes", None
                    )
                    if sub_target_attributes:
                        if not target_is_graph:
                            raise ValueError(
                                f"'{target_id}' is not a graph so 'sub_target_attributes' should not be specified"
                            )
                        if target in update_attrs:
                            update_attrs[target].update(sub_target_attributes)
                        else:
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
        if attrs:
            node_attrs = graph.nodes[node]
            dict_merge(node_attrs, attrs, overwrite=True)
