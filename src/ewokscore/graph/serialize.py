import importlib
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Optional
from typing import Tuple
from typing import Union

try:
    from enum import StrEnum
except ImportError:
    from backports.strenum import StrEnum
import networkx
from ewoksutils.path_utils import makedirs_from_filename
from packaging.version import Version

from .. import node
from .._serialization import json
from .._serialization import yaml
from .._serialization.common.utils import types
from .models import GraphSource
from .schema import normalize_schema_version

logger = logging.getLogger(__name__)


class GraphRepresentation(StrEnum):
    json = "json"  # only JSON types (file)
    json_dict = "json_dict"  # python types
    json_string = "json_string"  # only JSON types
    json_module = "json_module"  # only JSON types
    yaml = "yaml"  # only JSON types
    yaml_module = "yaml_module"  # only yaml types
    test_core = "test_core"  # python types


network_x_version = Version(networkx.__version__)


def dump(
    graph: networkx.DiGraph,
    destination: Optional[Union[str, Path]] = None,
    representation: Optional[Union[GraphRepresentation, str]] = None,
    serializer: Optional[Union[types.GraphSerializer, str]] = None,
    **save_options,
) -> Union[str, Path, dict]:
    """From runtime to persistent representation"""
    if isinstance(representation, str):
        representation = GraphRepresentation(representation)
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
        dictrepr = dump(graph, representation=GraphRepresentation.json_dict)

        makedirs_from_filename(destination)
        save_options.setdefault("indent", 2)
        with open(destination, mode="w") as f:
            json.dump(
                dictrepr,
                f,
                item_serializers=_ITEM_SERIALIZERS,
                serializer=serializer,
                insert_serialize_info=_insert_serialize_info,
                **save_options,
            )
        return destination

    if representation == GraphRepresentation.json_string:
        dictrepr = dump(graph, representation=GraphRepresentation.json_dict)

        return json.dumps(
            dictrepr,
            item_serializers=_ITEM_SERIALIZERS,
            serializer=serializer,
            insert_serialize_info=_insert_serialize_info,
            **save_options,
        )

    if representation == GraphRepresentation.yaml:
        if destination is None:
            raise TypeError("Destination should be specified when dumping to yaml")
        dictrepr = dump(graph, representation=GraphRepresentation.json_dict)

        makedirs_from_filename(destination)
        with open(destination, mode="w") as f:
            yaml.dump(
                dictrepr,
                f,
                item_serializers=_ITEM_SERIALIZERS,
                serializer=serializer,
                insert_serialize_info=_insert_serialize_info,
                **save_options,
            )
        return destination

    if representation == GraphRepresentation.json_module:
        if destination is None:
            raise TypeError("Destination should be specified when dumping to json")
        package, _, file = str(destination).rpartition(".")
        assert package, f"No package provided when saving graph to '{destination}'"

        destination = os.path.join(_package_path(package), f"{file}.json")
        return dump(
            graph,
            destination=destination,
            representation=GraphRepresentation.json,
            serializer=serializer,
            **save_options,
        )

    if representation == GraphRepresentation.yaml_module:
        if destination is None:
            raise TypeError("Destination should be specified when dumping to yaml")
        package, _, file = str(destination).rpartition(".")
        assert package, f"No package provided when saving graph to '{destination}'"

        destination = os.path.join(_package_path(package), f"{file}.yaml")
        return dump(
            graph,
            destination=destination,
            representation=GraphRepresentation.yaml,
            serializer=serializer,
            **save_options,
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
        representation = GraphRepresentation(representation)

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
        return load(
            graph_dict,
            representation=GraphRepresentation.json_dict,
            root_dir=root_dir,
            root_module=root_module,
        )
    elif representation == GraphRepresentation.json_string:
        graph_dict = json_load(source)
        return load(
            graph_dict,
            representation=GraphRepresentation.json_dict,
            root_dir=root_dir,
            root_module=root_module,
        )
    elif representation == GraphRepresentation.yaml:
        graph_dict = _read_yaml_file(source, root_dir=root_dir, root_module=root_module)
        return load(
            graph_dict,
            representation=GraphRepresentation.json_dict,
            root_dir=root_dir,
            root_module=root_module,
        )
    elif representation == GraphRepresentation.json_module:
        package, _, source = source.rpartition(".")
        if package:
            source = os.path.join(_package_path(package), source)
        return load(
            source,
            representation=GraphRepresentation.json,
            root_dir=root_dir,
            root_module=root_module,
        )
    elif representation == GraphRepresentation.yaml_module:
        package, _, source = source.rpartition(".")
        if package:
            source = os.path.join(_package_path(package), source)
        return load(
            source,
            representation=GraphRepresentation.yaml,
            root_dir=root_dir,
            root_module=root_module,
        )
    elif representation == GraphRepresentation.test_core:
        from ..tests.examples.graphs import get_graph

        return load(get_graph(source)[0], GraphRepresentation.json_dict)
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
    filename, graph_id = _find_graph_path(
        filename,
        root_dir=root_dir,
        root_module=root_module,
        possible_extensions=(".json",),
    )
    with open(filename, mode="r") as f:
        return _overwrite_graph_id(json_load(f), graph_id)


def _read_yaml_file(
    filename: str, root_dir: Optional[str] = None, root_module: Optional[str] = None
) -> dict:
    filename, graph_id = _find_graph_path(
        filename,
        root_dir=root_dir,
        root_module=root_module,
        possible_extensions=(".yml", ".yaml"),
    )
    with open(filename, mode="r") as f:
        return _overwrite_graph_id(_yaml_load(f), graph_id)


def _read_any_file(
    filename: Union[str, Path],
    root_dir: Optional[Union[str, Path]] = None,
    root_module: Optional[str] = None,
) -> Optional[dict]:
    filename, graph_id = _find_graph_path(
        filename,
        root_dir=root_dir,
        root_module=root_module,
        possible_extensions=(".json", ".yml", ".yaml"),
    )
    with open(filename, mode="r") as f:
        content = f.read()

    try:
        return _overwrite_graph_id(json_load(content), graph_id)
    except types.EwoksDecodeError:
        pass

    try:
        return _overwrite_graph_id(_yaml_load(content), graph_id)
    except types.EwoksDecodeError:
        pass

    raise ValueError(f"File format of '{filename}' not supported")


def json_load(content) -> dict:
    if isinstance(content, str):
        result = json.loads(
            content,
            item_deserializers=_ITEM_DESERIALIZERS,
            pop_serialize_info=_pop_serialize_info,
        )
    else:
        result = json.load(
            content,
            item_deserializers=_ITEM_DESERIALIZERS,
            pop_serialize_info=_pop_serialize_info,
        )
    if not isinstance(result, Mapping):
        raise TypeError("graph must be a dictionary")
    return result


def _yaml_load(content) -> dict:
    if isinstance(content, str):
        result = yaml.loads(
            content,
            item_deserializers=_ITEM_DESERIALIZERS,
            pop_serialize_info=_pop_serialize_info,
        )
    else:
        result = yaml.load(
            content,
            item_deserializers=_ITEM_DESERIALIZERS,
            pop_serialize_info=_pop_serialize_info,
        )
    if not isinstance(result, Mapping):
        raise TypeError("graph must be a dictionary")
    return result


def _find_graph_path(
    path: Union[str, Path],
    root_dir: Optional[Union[str, Path]] = None,
    root_module: Optional[str] = None,
    possible_extensions: Tuple[str, ...] = tuple(),
) -> Tuple[str, Optional[str]]:
    """When the :code:`path` is relative, the parent directory is assumed to be
    (in order of priority):

    * :code:`root_dir`
    * :code:`root_module` directory
    * current working directory

    When :code:`path` is not found it tries to find the path with a different
    extension from :code:`possible_extensions`.

    :param path: could be a relative path, might have no extension
    :param root_dir: in case :code:`path` is relative
    :param root_module: in case :code:`root_dir` is not provided
    :param possible_extensions: in case :code:`path` is not found
    :returns: file path and graph identifier
    :raises: FileNotFoundError
    """
    # From python module
    if not root_dir and root_module:
        root_dir = _package_path(root_module)
    else:
        root_module = None

    # Absolute path
    if not os.path.isabs(path) and root_dir:
        path = os.path.join(root_dir, path)
    path = os.path.abspath(path)

    if os.path.exists(path):
        graph_id = _graph_id_from_package_data_path(root_module, path)
        return path, graph_id

    # Try different extensions
    root, _ = os.path.splitext(path)
    for new_ext in possible_extensions:
        new_full_path = root + new_ext
        if os.path.exists(new_full_path):
            graph_id = _graph_id_from_package_data_path(root_module, new_full_path)
            return new_full_path, graph_id

    raise FileNotFoundError(path)


def _graph_id_from_package_data_path(
    root_module: Optional[str], path: str
) -> Optional[str]:
    if root_module is None:
        return None
    stem = os.path.splitext(os.path.basename(path))[0]
    return f"{root_module}.{stem}"


def _overwrite_graph_id(graph_dict: dict, graph_id: Optional[str]) -> dict:
    if graph_id is None:
        return graph_dict
    graph_dict.setdefault("graph", {})["id"] = graph_id
    return graph_dict


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


def _insert_serialize_info(
    graph: dict, key: str, serialize_info: types.SerializeInfo
) -> dict:
    graph[key] = serialize_info.serialize()
    return graph


def _pop_serialize_info(graph: dict, key: str) -> Optional[types.SerializeInfo]:
    serialize_info = graph.get(key)
    if serialize_info:
        return types.SerializeInfo.deserialize(serialize_info)


_ITEM_SERIALIZERS = {
    ("graph", "input_nodes", "*", "id"): node.as_json_node_id_type,
    ("graph", "input_nodes", "*", "node"): node.as_json_node_id_type,
    ("graph", "input_nodes", "*", "sub_node"): node.as_json_node_id_type,
    ("graph", "output_nodes", "*", "id"): node.as_json_node_id_type,
    ("graph", "output_nodes", "*", "node"): node.as_json_node_id_type,
    ("graph", "output_nodes", "*", "sub_node"): node.as_json_node_id_type,
    ("nodes", "*", "id"): node.as_json_node_id_type,
    ("nodes", "*", "node"): node.as_json_node_id_type,
    ("links", "*", "source"): node.as_json_node_id_type,
    ("links", "*", "target"): node.as_json_node_id_type,
    ("links", "*", "sub_source"): node.as_json_node_id_type,
    ("links", "*", "sub_target"): node.as_json_node_id_type,
}


_ITEM_DESERIALIZERS = {
    ("graph", "input_nodes", "*", "id"): node.as_node_id_type,
    ("graph", "input_nodes", "*", "node"): node.as_node_id_type,
    ("graph", "input_nodes", "*", "sub_node"): node.as_node_id_type,
    ("graph", "output_nodes", "*", "id"): node.as_node_id_type,
    ("graph", "output_nodes", "*", "node"): node.as_node_id_type,
    ("graph", "output_nodes", "*", "sub_node"): node.as_node_id_type,
    ("nodes", "*", "id"): node.as_node_id_type,
    ("nodes", "*", "node"): node.as_node_id_type,
    ("links", "*", "source"): node.as_node_id_type,
    ("links", "*", "target"): node.as_node_id_type,
    ("links", "*", "sub_source"): node.as_node_id_type,
    ("links", "*", "sub_target"): node.as_node_id_type,
}
