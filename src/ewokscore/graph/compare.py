from typing import List
from typing import Sequence

import networkx


def graphs_are_equal(graph1: networkx.DiGraph, graph2: networkx.DiGraph) -> bool:
    if not _attrs_are_equal(graph1.graph, graph2.graph):
        return False
    if set(graph1.nodes) != set(graph2.nodes):
        return False
    for node_id, node_attr1 in graph1.nodes.items():
        node_attr2 = graph2.nodes[node_id]
        if not _attrs_are_equal(node_attr1, node_attr2):
            return False
    if set(graph1.edges) != set(graph2.edges):
        return False
    for edge_id, edge_attrs1 in graph1.edges.items():
        edge_attrs2 = graph2.edges[edge_id]
        if not _attrs_are_equal(edge_attrs1, edge_attrs2):
            return False
    return True


def _attrs_are_equal(attrs1: dict, attrs2: dict) -> bool:
    if set(attrs1) != set(attrs2):
        return False
    for name, value1 in attrs1.items():
        value2 = attrs2[name]
        if name in ("input_nodes", "output_nodes"):
            value1 = _items_to_dict(value1, ["id"])
            value2 = _items_to_dict(value2, ["id"])
        elif name == "default_inputs":
            value1 = _items_to_dict(value1, ["name"])
            value2 = _items_to_dict(value2, ["name"])
        elif name == "data_mapping":
            value1 = _items_to_dict(value1, ["source_output", "target_input"])
            value2 = _items_to_dict(value2, ["source_output", "target_input"])
        elif name == "conditions":
            value1 = _items_to_dict(value1, ["source_output"])
            value2 = _items_to_dict(value2, ["source_output"])
        if value1 != value2:
            return False
    return True


def _items_to_dict(items: List[dict], keys: Sequence[str]) -> dict:
    result = dict()
    for item in items:
        result[tuple(item[k] for k in keys)] = item
    return result
