import os
import enum
import json
import yaml
import logging
from typing import Optional, Union
from collections.abc import Mapping
import importlib

import networkx
from ewoksutils.path_utils import makedirs_from_filename

from ..node import node_id_from_json
from .schema import normalize_schema_version

logger = logging.getLogger(__name__)

GraphRepresentation = enum.Enum(
    "GraphRepresentation", "json json_dict json_string json_module yaml"
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


def graph_full_path(path, root_dir=None, root_module=None, possible_extensions=tuple()):
    if not root_dir and root_module:
        root_dir = _package_path(root_module)
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


def dump(
    graph: networkx.DiGraph,
    destination=None,
    representation: Optional[Union[GraphRepresentation, str]] = None,
    **kw,
) -> Union[str, dict]:
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
        return _networkx_to_dict(graph)
    elif representation == GraphRepresentation.json:
        dictrepr = dump(graph)
        makedirs_from_filename(destination)
        with open(destination, mode="w") as f:
            json.dump(dictrepr, f, **kw)
        return destination
    elif representation == GraphRepresentation.json_string:
        dictrepr = dump(graph)
        return json.dumps(dictrepr, **kw)
    elif representation == GraphRepresentation.yaml:
        dictrepr = dump(graph)
        makedirs_from_filename(destination)
        with open(destination, mode="w") as f:
            yaml.dump(dictrepr, f, **kw)
        return destination
    elif representation == GraphRepresentation.json_module:
        package, _, file = destination.rpartition(".")
        assert package, f"No package provided when saving graph to '{destination}'"
        destination = os.path.join(_package_path(package), f"{file}.json")
        return dump(graph, destination=destination, representation="json", **kw)
    else:
        raise TypeError(representation, type(representation))


def load(
    source=None,
    representation: Optional[Union[GraphRepresentation, str]] = None,
    root_dir: Optional[str] = None,
    root_module: Optional[str] = None,
) -> networkx.DiGraph:
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
        graph = _dict_to_networkx(source)
    elif representation == GraphRepresentation.json:
        source = graph_full_path(
            source,
            root_dir=root_dir,
            root_module=root_module,
            possible_extensions=(".json",),
        )
        with open(source, mode="r") as f:
            source = json.load(f, object_pairs_hook=ewoks_jsonload_hook)
        graph = _dict_to_networkx(source)
    elif representation == GraphRepresentation.json_string:
        source = json.loads(source, object_pairs_hook=ewoks_jsonload_hook)
        graph = _dict_to_networkx(source)
    elif representation == GraphRepresentation.yaml:
        source = graph_full_path(
            source,
            root_dir=root_dir,
            root_module=root_module,
            possible_extensions=(".yml", ".yaml"),
        )
        with open(source, mode="r") as f:
            source = yaml.load(f, yaml.Loader)
        graph = _dict_to_networkx(source)
    elif representation == GraphRepresentation.json_module:
        package, _, source = source.rpartition(".")
        if package:
            source = os.path.join(_package_path(package), source)
        return load(
            source,
            representation="json",
            root_dir=root_dir,
            root_module=root_module,
        )
    else:
        raise TypeError(representation, type(representation))

    if not networkx.is_directed(graph):
        raise TypeError(graph, type(graph))

    return graph


def _package_path(package: str) -> str:
    package = importlib.import_module(package)
    return package.__path__[0]


def _dict_to_networkx(graph: dict) -> networkx.DiGraph:
    graph.setdefault("directed", True)
    graph.setdefault("nodes", list())
    graph.setdefault("links", list())
    graph.setdefault("graph", dict())

    if not graph["graph"].get("id"):
        logger.warning('Graph has no "id": use "notspecified"')
        graph["graph"]["id"] = "notspecified"
    normalize_schema_version(graph)

    return networkx.readwrite.json_graph.node_link_graph(graph)


def _networkx_to_dict(graph: networkx.DiGraph) -> dict:
    return networkx.readwrite.json_graph.node_link_data(graph)
