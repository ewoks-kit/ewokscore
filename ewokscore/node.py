from typing import Union


def flatten_node_name(node_name: Union[str, int, tuple]) -> tuple:
    if isinstance(node_name, str):
        return (node_name,)
    elif isinstance(node_name, int):
        return str(node_name)
    elif len(node_name) == 1:
        return (node_name[0],)
    else:
        return (node_name[0],) + flatten_node_name(node_name[1])


def node_name_as_string(node_name: Union[str, int, tuple], sep=":") -> str:
    return sep.join(flatten_node_name(node_name))


def node_name_from_json(node_name):
    if isinstance(node_name, list):
        return tuple(map(node_name_from_json, node_name))
    return node_name
