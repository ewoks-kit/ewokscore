import os
import enum
import json
import yaml
import networkx
from typing import Optional, Union
from collections.abc import Mapping

from ..node import node_id_from_json

GraphRepresentation = enum.Enum(
    "GraphRepresentation", "json json_dict json_string yaml"
)


def _ewoks_jsonload_hook_pair(item):
    key, value = item
    if key in (
        "source",
        "target",
        "sub_source",
        "sub_target",
        "id",
        "node",
        "sub_node",
    ):
        value = node_id_from_json(value)
    return key, value


def ewoks_jsonload_hook(items):
    return dict(map(_ewoks_jsonload_hook_pair, items))


def graph_full_path(path, root_dir=None, possible_extensions=tuple()):
    if not os.path.isabs(path) and root_dir:
        path = os.path.join(root_dir, path)
    path = os.path.abspath(path)
    if os.path.exists(path):
        return path
    root, _ = os.path.splitext(path)
    for new_ext in possible_extensions:
        new_full_path = root + new_ext
        if os.path.exists(new_full_path):
            return new_full_path
    raise FileNotFoundError(path)


def set_graph_defaults(graph_as_dict):
    graph_as_dict.setdefault("directed", True)
    graph_as_dict.setdefault("nodes", list())
    graph_as_dict.setdefault("links", list())


def dump(
    graph: networkx.DiGraph,
    destination=None,
    representation: Optional[Union[GraphRepresentation, str]] = None,
    **kw,
) -> Optional[str]:
    """From runtime to persistent representation"""
    if isinstance(representation, str):
        representation = GraphRepresentation.__members__[representation]
    if representation is None:
        if isinstance(destination, str):
            filename = destination.lower()
            if filename.endswith(".json"):
                representation = GraphRepresentation.json
            elif filename.endswith((".yml", ".yaml")):
                representation = GraphRepresentation.yaml
        else:
            representation = GraphRepresentation.json_dict
    if representation == GraphRepresentation.json_dict:
        return networkx.readwrite.json_graph.node_link_data(graph)
    elif representation == GraphRepresentation.json:
        dictrepr = dump(graph)
        with open(destination, mode="w") as f:
            json.dump(dictrepr, f, **kw)
    elif representation == GraphRepresentation.json_string:
        dictrepr = dump(graph)
        return json.dumps(dictrepr, **kw)
    elif representation == GraphRepresentation.yaml:
        dictrepr = dump(graph)
        with open(destination, mode="w") as f:
            yaml.dump(dictrepr, f, **kw)
    else:
        raise TypeError(representation, type(representation))


def load(
    source=None,
    representation: Optional[Union[GraphRepresentation, str]] = None,
    root_dir: Optional[str] = None,
) -> None:
    """From persistent to runtime representation"""
    if isinstance(representation, str):
        representation = GraphRepresentation.__members__[representation]
    if representation is None:
        if isinstance(source, Mapping):
            representation = GraphRepresentation.json_dict
        elif isinstance(source, str):
            if "{" in source and "}" in source:
                representation = GraphRepresentation.json_string
            else:
                filename = source.lower()
                if filename.endswith(".json"):
                    representation = GraphRepresentation.json
                elif filename.endswith((".yml", ".yaml")):
                    representation = GraphRepresentation.yaml
                else:
                    representation = GraphRepresentation.json
    if not source:
        graph = networkx.DiGraph()
    elif isinstance(source, networkx.Graph):
        graph = source
    elif hasattr(source, "graph") and isinstance(source.graph, networkx.Graph):
        graph = source.graph
    elif representation == GraphRepresentation.json_dict:
        set_graph_defaults(source)
        graph = networkx.readwrite.json_graph.node_link_graph(source)
    elif representation == GraphRepresentation.json:
        source = graph_full_path(source, root_dir, possible_extensions=(".json",))
        with open(source, mode="r") as f:
            source = json.load(f, object_pairs_hook=ewoks_jsonload_hook)
        set_graph_defaults(source)
        graph = networkx.readwrite.json_graph.node_link_graph(source)
    elif representation == GraphRepresentation.json_string:
        source = json.loads(source, object_pairs_hook=ewoks_jsonload_hook)
        set_graph_defaults(source)
        graph = networkx.readwrite.json_graph.node_link_graph(source)
    elif representation == GraphRepresentation.yaml:
        source = graph_full_path(
            source, root_dir, possible_extensions=(".yml", ".yaml")
        )
        with open(source, mode="r") as f:
            source = yaml.load(f, yaml.Loader)
        set_graph_defaults(source)
        graph = networkx.readwrite.json_graph.node_link_graph(source)
    else:
        raise TypeError(representation, type(representation))

    if not networkx.is_directed(graph):
        raise TypeError(graph, type(graph))

    return graph
