"""
Serialized objects with custom serialization for certain dictionary keys and list items.
"""

from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

from .utils import types
from .utils.traversal import Traversal


def pre_serialize(
    obj: Any,
    item_serializers: Optional[Dict[types.Path, types.ConverterType]] = None,
) -> Any:
    """
    :param obj: object to serialize
    :param item_serializers: paths to nested dict/list item with associated custom value serialization
    """
    if not item_serializers:
        return obj

    t = Traversal(obj)

    while t.next():
        current = t.current

        # --- dict ---
        if isinstance(current, dict):
            new_dict = {}
            t.assign(new_dict)

            for k, v in reversed(list(current.items())):
                matched, new_val = _apply_converters(t.path, k, v, item_serializers)
                if matched:
                    new_dict[k] = new_val
                else:
                    t.append_dict_key(new_dict, k, v)
            continue

        # --- list ---
        if isinstance(current, list):
            new_list = [None] * len(current)
            t.assign(new_list)
            t.append_sequence_items(new_list, current)
            continue

        # --- fallback ---
        t.assign(current)

    return t.result


def post_deserialize(
    obj: Any,
    item_deserializers: Optional[Dict[types.Path, types.ConverterType]] = None,
) -> Any:
    """
    :param obj: object to deserialize
    :param item_deserializers: paths to nested dict/list item with associated custom value deserialization
    """
    if not item_deserializers:
        return obj

    t = Traversal(obj)

    while t.next():
        current = t.current

        # --- dict ---
        if isinstance(current, dict):
            new_dict = {}
            t.assign(new_dict)

            for k, v in reversed(list(current.items())):
                matched, new_val = _apply_converters(t.path, k, v, item_deserializers)
                if matched:
                    new_dict[k] = new_val
                else:
                    t.append_dict_key(new_dict, k, v)
            continue

        # --- list ---
        if isinstance(current, list):
            new_list = [None] * len(current)
            t.assign(new_list)
            t.append_sequence_items(new_list, current)
            continue

        # --- passthrough ---
        t.assign(current)

    return t.result


def _match_path(path: types.Path, pattern: types.PathPattern) -> bool:
    if len(path) != len(pattern):
        return False
    for p, pat in zip(path, pattern):
        if pat == "*":
            continue
        if p != pat:
            return False
    return True


def _apply_converters(
    path: types.Path,
    key: Union[str, int],
    value: Any,
    converters: Dict[types.Path, types.ConverterType],
) -> Tuple[bool, Any]:
    full_path = path + (key,)
    for pattern, converter in converters.items():
        if _match_path(full_path, pattern):
            return True, converter(value)
    return False, None
