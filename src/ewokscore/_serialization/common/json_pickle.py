"""
Serialized objects and handle types as follows

- `str`: preserve
- `int`: preserve
- `float`: preserve
- `bool`: preserve
- `list`: preserve
- `dict`: preserve
- `None`: preserve
- Else: pickle
"""

import base64
import pickle
from typing import Any

import numpy

from .utils import constants
from .utils import types
from .utils.container import MutableContainer
from .utils.convert import convert_if_equal
from .utils.traversal import Traversal


def pre_serialize(obj: Any) -> Any:
    t = Traversal(obj)

    while t.next():
        current = t.current

        # --- primitives ---
        if current is None or isinstance(current, (str, bool)):
            t.assign(current)
            continue

        if isinstance(current, numpy.generic):
            new = convert_if_equal(current, int)
            if new is not None:
                t.assign(new)
                continue
            new = convert_if_equal(current, float)
            if new is not None:
                t.assign(new)
                continue
        elif isinstance(current, int):
            t.assign(int(current))
            continue
        elif isinstance(current, float):
            t.assign(float(current))
            continue

        # --- dict ---
        if isinstance(current, dict):
            if constants.EWOKS_KEY in current:
                raise types.EwoksEncodeError(
                    f"Dictionary key '{constants.EWOKS_KEY}' is reserved"
                )

            new_dict = {}
            t.assign(new_dict)

            for k, v in reversed(list(current.items())):
                t.append_dict_key(new_dict, k, v)
            continue

        # --- list ---
        if isinstance(current, list):
            new_list = [None] * len(current)
            t.assign(new_list)
            t.append_sequence_items(new_list, current)
            continue

        # --- tuple ---
        if isinstance(current, tuple):
            new_obj = {
                constants.EWOKS_KEY: "tuple",
                "items": [None] * len(current),
            }
            t.assign(new_obj)
            t.append_sequence_items(new_obj["items"], list(current))
            continue

        # --- set ---
        if isinstance(current, set):
            new_obj = {
                constants.EWOKS_KEY: "set",
                "items": [None] * len(current),
            }
            t.assign(new_obj)
            t.append_sequence_items(new_obj["items"], list(current))
            continue

        # --- bytes ---
        if isinstance(current, (bytes, bytearray)):
            t.assign(
                {
                    constants.EWOKS_KEY: "bytes",
                    "data": base64.b64encode(bytes(current)).decode("ascii"),
                }
            )
            continue

        # --- fallback ---
        t.assign(
            {
                constants.EWOKS_KEY: "pickle",
                "data": base64.b64encode(pickle.dumps(current)).decode("ascii"),
            }
        )

    return t.result


def post_deserialize(obj: Any) -> Any:
    t = Traversal(obj)

    while t.next():
        current = t.current

        # --- dict ---
        if isinstance(current, dict):
            if constants.EWOKS_KEY not in current:
                new_dict = {}
                t.assign(new_dict)

                for k, v in reversed(list(current.items())):
                    t.append_dict_key(new_dict, k, v)
                continue

            tag = current[constants.EWOKS_KEY]

            if tag == "bytes":
                t.assign(base64.b64decode(current["data"].encode("ascii")))
                continue

            if tag == "tuple":
                items = current["items"]
                tmp = [None] * len(items)
                t.assign(tmp)

                t.append_dict_key(t.parent, t.key, MutableContainer(tmp, tuple))
                t.append_sequence_items(tmp, items)
                continue

            if tag == "set":
                items = current["items"]
                tmp = [None] * len(items)
                t.assign(tmp)

                t.append_dict_key(t.parent, t.key, MutableContainer(tmp, set))
                t.append_sequence_items(tmp, items)
                continue

            if tag == "pickle":
                t.assign(
                    pickle.loads(base64.b64decode(current["data"].encode("ascii")))
                )
                continue

            raise types.EwoksDecodeError(
                f"Unknown '{constants.EWOKS_KEY}' tag in {current}"
            )

        # --- list ---
        if isinstance(current, list):
            new_list = [None] * len(current)
            t.assign(new_list)
            t.append_sequence_items(new_list, current)
            continue

        # --- conversion of mutable containers ---
        if isinstance(current, MutableContainer):
            t.assign(current.get_container())
            continue

        # --- passthrough ---
        t.assign(current)

    return t.result
