"""
Instead of serializing to and from Python objects, we serialize to and from
EWOKS-JSON objects.

An EWOKS-JSON object only contains object types `str`, `int`, `float`, `bool`,
`list`, `dict` and `None`.
"""

import base64
import pickle
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional

import numpy


class EwoksEncodeError(Exception):
    pass


class EwoksDecodeError(Exception):
    pass


def pre_serialize(
    obj: Any, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None
) -> Any:
    """
    Convert Python object to an EWOKS-JSON object.
    """
    if obj is None or isinstance(obj, (str, bool)):
        return obj

    if isinstance(obj, numpy.generic):
        for vtype in (int, float):
            try:
                robj = vtype(obj)
                if obj == robj:
                    return robj
            except Exception:
                pass
    elif isinstance(obj, int):
        return int(obj)
    elif isinstance(obj, float):
        return float(obj)

    if isinstance(obj, dict):
        if _EWOKS_KEY in obj:
            raise EwoksEncodeError(
                f"Dictionary key '{_EWOKS_KEY}' is reserved for custom type serialization"
            )
        return _parse_dict(obj, pre_serialize, special_keys)

    if isinstance(obj, list):
        return [pre_serialize(x, special_keys=special_keys) for x in obj]

    if isinstance(obj, tuple):
        return {
            _EWOKS_KEY: "tuple",
            "items": [pre_serialize(x, special_keys=special_keys) for x in obj],
        }

    if isinstance(obj, set):
        return {
            _EWOKS_KEY: "set",
            "items": [pre_serialize(x, special_keys=special_keys) for x in obj],
        }

    if isinstance(obj, (bytes, bytearray)):
        return {
            _EWOKS_KEY: "bytes",
            "data": base64.b64encode(bytes(obj)).decode("ascii"),
        }

    return {
        _EWOKS_KEY: "pickle",
        "data": base64.b64encode(pickle.dumps(obj)).decode("ascii"),
    }


def post_deserialize(
    obj: Any, special_keys: Optional[Dict[str, Callable[[str], Any]]] = None
) -> Any:
    """
    Convert an EWOKS-JSON object to Python object.
    """
    if isinstance(obj, dict):
        if _EWOKS_KEY not in obj:
            return _parse_dict(obj, post_deserialize, special_keys)

        tag = obj[_EWOKS_KEY]

        if tag == "bytes":
            return base64.b64decode(obj["data"].encode("ascii"))

        if tag == "tuple":
            return tuple(
                post_deserialize(x, special_keys=special_keys) for x in obj["items"]
            )

        if tag == "set":
            return set(
                post_deserialize(x, special_keys=special_keys) for x in obj["items"]
            )

        if tag == "pickle":
            return pickle.loads(base64.b64decode(obj["data"].encode("ascii")))

        raise EwoksDecodeError(f"Unknown '{_EWOKS_KEY}' tag in {obj}")

    if isinstance(obj, list):
        return [post_deserialize(x, special_keys=special_keys) for x in obj]

    return obj


_EWOKS_KEY = "__ewoks__"


def _parse_dict(
    obj: Dict[str, Any],
    parser: Callable[[Any], Any],
    special_keys: Optional[Dict[str, Callable[[Any], Any]]],
) -> Any:
    result = {}
    special_keys = special_keys or {}
    for k, v in obj.items():
        if k in special_keys:
            result[k] = special_keys[k](v)
        else:
            result[k] = parser(v, special_keys=special_keys)
    return result
