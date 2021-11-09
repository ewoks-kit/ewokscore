from typing import Union

NodeIdType = Union[str, int, tuple]


def flatten_node_id(node_id: NodeIdType) -> tuple:
    if isinstance(node_id, str):
        return (node_id,)
    elif isinstance(node_id, int):
        return str(node_id)
    elif len(node_id) == 1:
        return (node_id[0],)
    else:
        return (node_id[0],) + flatten_node_id(node_id[1])


def node_id_as_string(node_id: NodeIdType, sep=":") -> str:
    return sep.join(flatten_node_id(node_id))


def node_id_from_json(node_id):
    if isinstance(node_id, list):
        return tuple(map(node_id_from_json, node_id))
    return node_id


def get_node_label(node_attrs: dict, node_id: NodeIdType = ""):
    node_label = node_attrs.get("label")
    if node_label:
        return node_label
    return node_id_as_string(node_id)
