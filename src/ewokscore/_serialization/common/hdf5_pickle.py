"""
Serialized objects and handle types as follows

- `str`: preserve
- `int`: preserve
- `float`: preserve
- `bool`: preserve
- `list`: preserve
- `dict`: preserve
- `None`: preserve
- `numpy.ndarray`: preserve
- `numpy.generic`: preserve if integer or float
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

            t.assign_dict(current)
            continue

        # --- list ---
        if isinstance(current, list) and _is_scalar_sequence(current):
            new_obj = {
                constants.EWOKS_KEY: "list",
                "items": [None] * len(current),
            }
            t.assign(new_obj)
            t.append_sequence(new_obj["items"], current)
            continue

        # --- tuple ---
        if isinstance(current, tuple) and _is_scalar_sequence(current):
            new_obj = {
                constants.EWOKS_KEY: "tuple",
                "items": [None] * len(current),
            }
            t.assign(new_obj)
            t.append_sequence(new_obj["items"], current)
            continue

        # --- set ---
        if isinstance(current, set) and _is_scalar_sequence(current):
            new_obj = {
                constants.EWOKS_KEY: "set",
                "items": [None] * len(current),
            }
            t.assign(new_obj)
            t.append_sequence(new_obj["items"], current)
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
                t.assign_dict(current)
                continue

            tag = current[constants.EWOKS_KEY].item()

            if tag == "bytes":
                t.assign(base64.b64decode(current["data"].item()))
                continue

            if tag == "list":
                items = current["items"]
                tmp = [None] * len(items)
                t.assign(tmp)

                t.append(t.parent, t.key, MutableContainer(tmp, list))
                t.append_sequence(tmp, items)
                continue

            if tag == "tuple":
                items = current["items"]
                tmp = [None] * len(items)
                t.assign(tmp)

                t.append(t.parent, t.key, MutableContainer(tmp, tuple))
                t.append_sequence(tmp, items)
                continue

            if tag == "set":
                items = current["items"]
                tmp = [None] * len(items)
                t.assign(tmp)

                t.append(t.parent, t.key, MutableContainer(tmp, set))
                t.append_sequence(tmp, items)
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
            t.assign_sequence(current)
            continue

        # --- conversion of mutable containers ---
        if isinstance(current, MutableContainer):
            t.assign(current.get_container())
            continue

        # --- passthrough ---
        t.assign(current)

    return t.result


def _is_scalar_sequence(value: Any) -> bool:
    return all(
        isinstance(item, (str, bytes, int, float, numpy.generic)) for item in value
    )
