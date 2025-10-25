import enum
import importlib
import json
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Optional
from typing import Tuple
from typing import Union

import networkx
import yaml
from ewoksutils.deprecation_utils import deprecated
from ewoksutils.path_utils import makedirs_from_filename
from packaging.version import Version

from ..node import node_id_from_json
from .models import GraphSource
from .schema import normalize_schema_version

logger = logging.getLogger(__name__)

GraphRepresentation = enum.Enum(
    "GraphRepresentation", "json json_dict json_string json_module yaml test_core"
)

network_x_version = Version(networkx.__version__)


def dump(
    graph: networkx.DiGraph,
    destination: Optional[Union[str, Path]] = None,
    representation: Optional[Union[GraphRepresentation, str]] = None,
    **save_options,
) -> Union[str, Path, dict]:
    """From runtime to persistent representation"""
    if isinstance(representation, str):
        representation = GraphRepresentation.__members__[representation]
    if representation is None:
        if isinstance(destination, (str, Path)):
            filename = str(destination).lower()
            if filename.endswith(".json"):
                representation = GraphRepresentation.json
            elif filename.endswith((".yml", ".yaml")):
                representation = GraphRepresentation.yaml
        else:
            representation = GraphRepresentation.json_dict

    if representation == GraphRepresentation.json_dict:
        return _networkx_to_dict(graph)

    if representation == GraphRepresentation.json:
        if destination is None:
            raise TypeError("Destination should be specified when dumping to json")
        dictrepr = dump(graph)
        makedirs_from_filename(destination)
        save_options.setdefault("indent", 2)
        with open(destination, mode="w") as f:
            json.dump(dictrepr, f, **save_options)
        return destination

    if representation == GraphRepresentation.json_string:
        dictrepr = dump(graph)
        return json.dumps(dictrepr, **save_options)

    if representation == GraphRepresentation.yaml:
        if destination is None:
            raise TypeError("Destination should be specified when dumping to yaml")
        dictrepr = dump(graph)
        makedirs_from_filename(destination)
        with open(destination, mode="w") as f:
            yaml.dump(dictrepr, f, **save_options)
        return destination

    if representation == GraphRepresentation.json_module:
        if destination is None:
            raise TypeError("Destination should be specified when dumping to json")
        package, _, file = str(destination).rpartition(".")
        assert package, f"No package provided when saving graph to '{destination}'"
        destination = os.path.join(_package_path(package), f"{file}.json")
        return dump(
            graph, destination=destination, representation="json", **save_options
        )

    if representation == GraphRepresentation.test_core:
        raise TypeError("'test_core' workflows representations cannot be saved")

    raise TypeError(representation, type(representation))


def load(
    source: Optional[GraphSource] = None,
    representation: Optional[Union[GraphRepresentation, str]] = None,
    root_dir: Optional[Union[str, Path]] = None,
    root_module: Optional[str] = None,
) -> networkx.DiGraph:
    """From persistent to runtime representation"""
    if isinstance(representation, str):
        representation = GraphRepresentation.__members__[representation]

    if representation is None:
        if isinstance(source, Mapping):
            representation = GraphRepresentation.json_dict
        elif isinstance(source, (str, Path)):
            if isinstance(source, str) and "{" in source and "}" in source:
                representation = GraphRepresentation.json_string
            else:
                filename = str(source).lower()
                if filename.endswith(".json"):
                    representation = GraphRepresentation.json
                elif filename.endswith((".yml", ".yaml")):
                    representation = GraphRepresentation.yaml
                else:
                    source = _read_any_file(
                        source, root_dir=root_dir, root_module=root_module
                    )
                    representation = GraphRepresentation.json_dict

    if not source:
        graph = networkx.DiGraph()
    elif isinstance(source, networkx.Graph):
        graph = source
    elif hasattr(source, "graph") and isinstance(source.graph, networkx.Graph):
        graph = source.graph
    elif representation == GraphRepresentation.json_dict:
        graph = _dict_to_networkx(source)
    elif representation == GraphRepresentation.json:
        graph_dict = _read_json_file(source, root_dir=root_dir, root_module=root_module)
        graph = _dict_to_networkx(graph_dict)
    elif representation == GraphRepresentation.json_string:
        graph_dict = json_load(source)
        graph = _dict_to_networkx(graph_dict)
    elif representation == GraphRepresentation.yaml:
        graph_dict = _read_yaml_file(source, root_dir=root_dir, root_module=root_module)
        graph = _dict_to_networkx(graph_dict)
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
    elif representation == GraphRepresentation.test_core:
        from ..tests.examples.graphs import get_graph

        return load(get_graph(source)[0], representation="json_dict")
    else:
        raise TypeError(representation, type(representation))

    if not networkx.is_directed(graph):
        raise TypeError(graph, type(graph))

    return graph


def _read_json_file(
    filename: Union[str, Path],
    root_dir: Optional[Union[str, Path]] = None,
    root_module: Optional[str] = None,
) -> dict:
    filename = _find_graph_path(
        filename,
        root_dir=root_dir,
        root_module=root_module,
        possible_extensions=(".json",),
    )
    with open(filename, mode="r") as f:
        return json_load(f)


def _read_yaml_file(
    filename: str, root_dir: Optional[str] = None, root_module: Optional[str] = None
) -> dict:
    filename = _find_graph_path(
        filename,
        root_dir=root_dir,
        root_module=root_module,
        possible_extensions=(".yml", ".yaml"),
    )
    with open(filename, mode="r") as f:
        return _yaml_load(f)


def _read_any_file(
    filename: Union[str, Path],
    root_dir: Optional[Union[str, Path]] = None,
    root_module: Optional[str] = None,
) -> Optional[dict]:
    filename = _find_graph_path(
        filename,
        root_dir=root_dir,
        root_module=root_module,
        possible_extensions=(".json", ".yml", ".yaml"),
    )
    with open(filename, mode="r") as f:
        content = f.read()

    try:
        return json_load(content)
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        return _yaml_load(content)
    except (yaml.YAMLError, TypeError):
        pass

    raise ValueError(f"File format of '{filename}' not supported")


def json_load(content) -> dict:
    if isinstance(content, str):
        result = json.loads(content, object_pairs_hook=_ewoks_jsonload_hook)
    else:
        result = json.load(content, object_pairs_hook=_ewoks_jsonload_hook)
    if not isinstance(result, Mapping):
        raise TypeError("graph must be a dictionary")
    return result


def _yaml_load(content) -> dict:
    result = yaml.load(content, yaml.Loader)
    if not isinstance(result, Mapping):
        raise TypeError("graph must be a dictionary")
    return result


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


@deprecated("Use 'json_load' instead")
def ewoks_jsonload_hook(items):
    return _ewoks_jsonload_hook(items)


def _ewoks_jsonload_hook(items):
    return dict(map(_ewoks_jsonload_hook_pair, items))


def _find_graph_path(
    path: Union[str, Path],
    root_dir: Optional[Union[str, Path]] = None,
    root_module: Optional[str] = None,
    possible_extensions: Tuple[str] = tuple(),
) -> str:
    """When the :code:`path` is relative, the parent directory is assumed to be
    (in order of priority):

    * :code:`root_dir`
    * :code:`root_module` directory
    * current working directory

    When :code:`path` is not found it tries to find the path with a different
    extension from :code:`possible_extensions`.

    :param path: could be a relative path, might have no extension
    :param root_dir: in case :code:`path` is relative
    :param root_module: in case :code:`root_module` is not provided
    :param possible_extensions: in case :code:`path` is not found
    :raises: FileNotFoundError
    """
    # Absolute path
    if not root_dir and root_module:
        root_dir = _package_path(root_module)
    if not os.path.isabs(path) and root_dir:
        path = os.path.join(root_dir, path)
    path = os.path.abspath(path)

    if os.path.exists(path):
        return path

    # Try different extensions
    root, _ = os.path.splitext(path)
    for new_ext in possible_extensions:
        new_full_path = root + new_ext
        if os.path.exists(new_full_path):
            return new_full_path

    raise FileNotFoundError(path)


def _package_path(package: str) -> str:
    package = importlib.import_module(package)
    return package.__path__[0]


def _dict_to_networkx(graph: dict) -> networkx.DiGraph:
    graph.setdefault("directed", True)
    graph.setdefault("nodes", list())
    graph.setdefault("links", list())
    graph.setdefault("graph", dict())

    if "id" not in graph["graph"]:
        logger.warning('Graph has no "id": use "notspecified"')
        graph["graph"]["id"] = "notspecified"
    normalize_schema_version(graph)

    if network_x_version < Version("3.4rc"):
        return networkx.readwrite.json_graph.node_link_graph(graph)
    else:
        return networkx.readwrite.json_graph.node_link_graph(graph, edges="links")


def _networkx_to_dict(graph: networkx.DiGraph) -> dict:
    if network_x_version < Version("3.4rc"):
        graph_dict = networkx.readwrite.json_graph.node_link_data(graph)
    else:
        graph_dict = networkx.readwrite.json_graph.node_link_data(graph, edges="links")

    # Remove fields that are not part of the Ewoks spec
    graph_dict.pop("directed")
    graph_dict.pop("multigraph")
    return graph_dict
