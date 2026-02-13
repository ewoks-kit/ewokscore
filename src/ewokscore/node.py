from typing import Optional, Union

NodeIdType = Union[str, int, tuple]

SEPARATOR = ":"


def flatten_node_id(node_id: NodeIdType) -> tuple:
    if isinstance(node_id, str):
        return (node_id,)
    elif isinstance(node_id, int):
        return str(node_id)
    elif len(node_id) == 1:
        return (node_id[0],)
    else:
        return (node_id[0],) + flatten_node_id(node_id[1])


def node_id_as_string(node_id: NodeIdType, sep: Optional[str] = None) -> str:
    if sep is None:
        sep = SEPARATOR
    return sep.join(flatten_node_id(node_id))


def node_id_from_json(node_id: Union[list, NodeIdType]) -> NodeIdType:
    if isinstance(node_id, list):
        return tuple(map(node_id_from_json, node_id))
    return node_id


def get_node_id(
    node_id: Optional[NodeIdType], node_attrs: Optional[dict]
) -> Optional[NodeIdType]:
    if node_id is None and node_attrs:
        return node_attrs.get("id")
    return node_id


def get_node_label(
    node_id: Optional[NodeIdType], node_attrs: Optional[dict], sep: Optional[str] = None
) -> Optional[str]:
    if node_attrs:
        node_label = node_attrs.get("label")
        if node_label:
            return node_label
    node_id = get_node_id(node_id, node_attrs)
    if node_id:
        return node_id_as_string(node_id, sep=sep)
    return None


def get_varinfo(node_attrs: Optional[dict], varinfo: Optional[dict] = None) -> dict:
    """Makes a copy"""
    if varinfo is None:
        varinfo = dict()
    else:
        varinfo = dict(varinfo)
    if node_attrs:
        varinfo.update(node_attrs.get("varinfo", dict()))
    return varinfo


def get_task_identifier(node_attrs: Optional[dict], default: Optional[str] = None):
    if node_attrs:
        return node_attrs.get("task_identifier", default)
    return default
