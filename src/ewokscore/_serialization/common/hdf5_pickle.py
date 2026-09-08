"""
Serialized objects and handle types as follows

- `str`: preserve
- `int`: preserve
- `float`: preserve
- `bool`: preserve
- `dict`: preserve
- `None`: preserve
- `numpy.ndarray`: preserve
- `numpy.generic`: preserve if integer or float
- `list`, `tuple`, `set`: preserve when all items are scalars of the same kind, pickle otherwise
- Else: pickle
"""

import base64
import pickle
from typing import Any
from typing import Optional

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
        if current is None:
            # HDF5 has no representation for `None`
            t.assign({constants.EWOKS_KEY: "none"})
            continue

        if isinstance(current, (str, bool)):
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

        # --- numpy ---
        if isinstance(current, numpy.ndarray):
            t.assign(current)
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
        if isinstance(current, list) and _is_scalar_sequence(current):
            new_obj = {
                constants.EWOKS_KEY: "list",
                "items": [None] * len(current),
            }
            t.assign(new_obj)
            t.append_sequence_items(new_obj["items"], list(current))
            continue

        # --- tuple ---
        if isinstance(current, tuple) and _is_scalar_sequence(current):
            new_obj = {
                constants.EWOKS_KEY: "tuple",
                "items": [None] * len(current),
            }
            t.assign(new_obj)
            t.append_sequence_items(new_obj["items"], list(current))
            continue

        # --- set ---
        if isinstance(current, set) and _is_scalar_sequence(current):
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

            tag = current[constants.EWOKS_KEY].item()

            if tag == "none":
                t.assign(None)
                continue

            if tag == "bytes":
                t.assign(base64.b64decode(current["data"].item()))
                continue

            if tag == "list":
                items = current["items"]
                tmp = [None] * len(items)
                t.assign(tmp)

                t.append_dict_key(t.parent, t.key, MutableContainer(tmp, list))
                t.append_sequence_items(tmp, items)
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
                    pickle.loads(base64.b64decode(current["data"].item()))  # noqa: S301
                )
                continue

            raise types.EwoksDecodeError(
                f"Unknown '{constants.EWOKS_KEY}' tag in {current}"
            )

        # --- numpy ---
        if isinstance(current, numpy.ndarray):
            if current.ndim == 0:
                # silx/h5py returns ndarray for scalars
                t.assign(current.item())
            else:
                t.assign(current)
            continue

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


def _is_scalar_sequence(value: Any) -> bool:
    """Whether the sequence can be stored as a single HDF5 dataset without
    changing the type of its items."""
    kind = None
    for item in value:
        item_kind = _scalar_storage_kind(item)
        if item_kind is None:
            return False
        if kind is None:
            kind = item_kind
        elif item_kind != kind:
            return False
    return True


def _scalar_storage_kind(value: Any) -> Optional[str]:
    """HDF5 dataset kind in which the scalar can be stored, `None` when it has no
    scalar representation."""
    if isinstance(value, (bool, numpy.bool_)):
        return "bool"
    if isinstance(value, str):
        return "text"
    if isinstance(value, (bytes, bytearray)):
        return "bytes"
    if isinstance(value, numpy.generic):
        # "b" is excluded above, "U" and "S" are `str` and `bytes` subclasses
        return {"i": "int", "u": "int", "f": "float"}.get(value.dtype.kind)
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return None
