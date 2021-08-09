import itertools
from .utils import dict_merge
from .node import flatten_node_name


def _pop_subgraph_node_name(subgraph_name, link_attrs, source=True):
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

    return _append_sub_node(subgraph_name, subgraph_node_name)


def _append_sub_node(subgraph_name, subgraph_node_name):
    if isinstance(subgraph_name, tuple):
        parent, child = subgraph_name
        return parent, _append_sub_node(child, subgraph_node_name)
    else:
        return subgraph_name, subgraph_node_name


def _is_subgraph(node_name, subgraphs):
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


def _pop_subgraph_node_names(source_name, target_name, link_attrs, subgraphs):
    if _is_subgraph(source_name, subgraphs):
        source = _pop_subgraph_node_name(source_name, link_attrs, source=True)
    else:
        link_attrs.pop("source", None)
        source = source_name

    if _is_subgraph(target_name, subgraphs):
        target = _pop_subgraph_node_name(target_name, link_attrs, source=False)
        target_attributes = link_attrs.pop("node_attributes", None)
    else:
        link_attrs.pop("target", None)
        target = target_name
        link_attrs.pop("node_attributes", None)
        target_attributes = None

    return source, target, target_attributes


def _extract_subgraph_links(source_name, target_name, links, subgraphs):
    for link_attrs in links:
        link_attrs = dict(link_attrs)
        source, target, target_attributes = _pop_subgraph_node_names(
            source_name, target_name, link_attrs, subgraphs
        )
        sublinks = link_attrs.pop("links", None)
        if sublinks:
            yield from _extract_subgraph_links(source, target, sublinks, subgraphs)
        else:
            yield source, target, link_attrs, target_attributes


def extract_subgraphs(graph, subgraphs):
    # Edges between supergraph and subgraph or subgraph and subgraph
    edges = list()
    update_attrs = dict()
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
            links = graph[source_name][target_name].get("links", list())
            itlinks = _extract_subgraph_links(
                source_name, target_name, links, subgraphs
            )
            for source, target, link_attrs, target_attributes in itlinks:
                if target_attributes:
                    update_attrs[target] = target_attributes
                edges.append((source, target, link_attrs))

    graph.remove_nodes_from(subgraphs.keys())
    return edges, update_attrs


def add_subgraph_links(graph, edges, update_attrs):
    # Output from extract_subgraphs
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
