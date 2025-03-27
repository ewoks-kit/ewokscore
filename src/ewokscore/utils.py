import inspect
from collections.abc import Mapping, Sequence
from typing import List, Tuple


def dict_merge(
    destination, source, overwrite=False, _nodes=None, contatenate_sequences=False
):
    """Merge the source into the destination"""
    if _nodes is None:
        _nodes = tuple()
    for key, value in source.items():
        if key in destination:
            _nodes += (str(key),)
            if isinstance(destination[key], Mapping) and isinstance(value, Mapping):
                dict_merge(
                    destination[key],
                    value,
                    overwrite=overwrite,
                    _nodes=_nodes,
                    contatenate_sequences=contatenate_sequences,
                )
            elif value == destination[key]:
                continue
            elif overwrite:
                destination[key] = value
            elif (
                contatenate_sequences
                and isinstance(destination[key], Sequence)
                and isinstance(value, Sequence)
            ):
                destination[key] += value
            else:
                raise ValueError("Conflict at " + ".".join(_nodes))
        else:
            destination[key] = value


def is_namedtuple(type_: type) -> bool:
    if not type_.__bases__ == (tuple,) or not hasattr(type_, "_fields"):
        return False
    if not isinstance(type_._fields, tuple):
        return False
    return all(isinstance(field, str) for field in type_._fields)


def method_arguments(method) -> Tuple[List[str], List[str]]:
    sig = inspect.signature(method)
    required_input_names = list()
    optional_input_names = list()
    for name, param in sig.parameters.items():
        required = param.default is inspect._empty
        if param.kind == param.VAR_POSITIONAL:
            continue
        if param.kind == param.VAR_KEYWORD:
            continue
        if required:
            required_input_names.append(name)
        else:
            optional_input_names.append(name)
    return required_input_names, optional_input_names
