"""
Serialization to be executed before the final serialization (JSON, YAML, ...).

Serialized objects only contain the builtin python types
`str`, `int`, `float`, `bool`, `list`, `dict` and `None`.
"""

import base64
import pickle
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import Union

import numpy


class EwoksEncodeError(ValueError):
    pass


class EwoksDecodeError(ValueError):
    pass


def pre_serialize(
    obj: Any, special_keys: Optional[Dict[str, Callable[[Any], Any]]] = None
) -> Any:
    special_keys = special_keys or {}
    t = _Traversal(obj)

    while t.next():
        current = t.current

        # --- primitives ---
        if current is None or isinstance(current, (str, bool)):
            t.assign(current)
            continue

        if isinstance(current, numpy.generic):
            new = _convert_if_equal(current, int)
            if new is not None:
                t.assign(new)
                continue
            new = _convert_if_equal(current, float)
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
            if _EWOKS_KEY in current:
                raise EwoksEncodeError(f"Dictionary key '{_EWOKS_KEY}' is reserved")

            new_dict = {}
            t.assign(new_dict)

            for k, v in reversed(list(current.items())):
                if k in special_keys:
                    new_dict[k] = special_keys[k](v)
                else:
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
                _EWOKS_KEY: "tuple",
                "items": [None] * len(current),
            }
            t.assign(new_obj)
            t.append_sequence_items(new_obj["items"], list(current))
            continue

        # --- set ---
        if isinstance(current, set):
            items = list(current)
            new_obj = {
                _EWOKS_KEY: "set",
                "items": [None] * len(items),
            }
            t.assign(new_obj)
            t.append_sequence_items(new_obj["items"], items)
            continue

        # --- bytes ---
        if isinstance(current, (bytes, bytearray)):
            t.assign(
                {
                    _EWOKS_KEY: "bytes",
                    "data": base64.b64encode(bytes(current)).decode("ascii"),
                }
            )
            continue

        # --- fallback ---
        t.assign(
            {
                _EWOKS_KEY: "pickle",
                "data": base64.b64encode(pickle.dumps(current)).decode("ascii"),
            }
        )

    return t.result


def post_deserialize(
    obj: Any, special_keys: Optional[Dict[str, Callable[[Any], Any]]] = None
) -> Any:
    special_keys = special_keys or {}
    t = _Traversal(obj)

    while t.next():
        current = t.current

        # --- dict ---
        if isinstance(current, dict):
            if _EWOKS_KEY not in current:
                new_dict = {}
                t.assign(new_dict)

                for k, v in reversed(list(current.items())):
                    if k in special_keys:
                        new_dict[k] = special_keys[k](v)
                    else:
                        t.append_dict_key(new_dict, k, v)
                continue

            tag = current[_EWOKS_KEY]

            if tag == "bytes":
                t.assign(base64.b64decode(current["data"].encode("ascii")))
                continue

            if tag == "tuple":
                items = current["items"]
                tmp = [None] * len(items)
                t.assign(tmp)

                t.append_dict_key(t.parent, t.key, _MutableContainer(tmp, tuple))
                t.append_sequence_items(tmp, items)
                continue

            if tag == "set":
                items = current["items"]
                tmp = [None] * len(items)
                t.assign(tmp)

                t.append_dict_key(t.parent, t.key, _MutableContainer(tmp, set))
                t.append_sequence_items(tmp, items)
                continue

            if tag == "pickle":
                t.assign(
                    pickle.loads(base64.b64decode(current["data"].encode("ascii")))
                )
                continue

            raise EwoksDecodeError(f"Unknown '{_EWOKS_KEY}' tag in {current}")

        # --- list ---
        if isinstance(current, list):
            new_list = [None] * len(current)
            t.assign(new_list)
            t.append_sequence_items(new_list, current)
            continue

        # --- conversion of mutable containers ---
        if isinstance(current, _MutableContainer):
            t.assign(current.get_container())
            continue

        # --- passthrough ---
        t.assign(current)

    return t.result


_EWOKS_KEY = "__ewoks__"

_ParentType = Union[None, list, dict]
_KeyType = Union[None, int, str]


class _MutableContainer:
    def __init__(self, mutable: Any, convert: Callable[[Any], Any]):
        self._mutable = mutable
        self._convert = convert

    def get_container(self) -> Any:
        return self._convert(self._mutable)


class _Traversal:
    def __init__(self, root: Any):
        self._stack: List[Tuple[_ParentType, _KeyType, Any]] = [(None, None, root)]
        self._result = None
        self._parent: _ParentType = None
        self._key: _KeyType = None
        self._current = None

    @property
    def result(self) -> Any:
        return self._result

    @property
    def parent(self) -> _ParentType:
        return self._parent

    @property
    def key(self) -> _KeyType:
        return self._key

    @property
    def current(self) -> Any:
        return self._current

    def next(self) -> bool:
        if not self._stack:
            return False
        self._parent, self._key, self._current = self._stack.pop()
        return True

    def assign(self, value: Any) -> None:
        if self._parent is None:
            self._result = value
        else:
            self._parent[self._key] = value

    def append_dict_key(self, parent: _ParentType, key: _KeyType, value: Any) -> None:
        self._stack.append((parent, key, value))

    def append_sequence_items(self, parent: Any, items: Sequence) -> None:
        for key in reversed(range(len(items))):
            self._stack.append((parent, key, items[key]))


def _convert_if_equal(value: Any, new_type: Type) -> Optional[Any]:
    try:
        new_value = new_type(value)
        if value == new_value:
            return new_value
    except Exception:
        pass
