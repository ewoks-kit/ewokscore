"""
Serialized objects and handle types like python's json module as follows

- `str`: preserve
- `int`: preserve
- `float`: preserve
- `bool`: preserve
- `list`: preserve
- `dict`: preserve with keys converted to strings [*]
- `None`: preserve
- `tuple`: convert to list [*]
- Else: pass-through

[*] irreversible
"""

from typing import Any

from .utils.traversal import Traversal


def pre_serialize(obj: Any) -> Any:
    t = Traversal(obj)

    while t.next():
        current = t.current

        # --- dict ---
        if isinstance(current, dict):
            new_dict = {}
            t.assign(new_dict)
            for k, v in reversed(list(current.items())):
                t.append_dict_key(new_dict, str(k), v)
            continue

        # --- list/tuple ---
        if isinstance(current, (list, tuple)):
            new_list = [None] * len(current)
            t.assign(new_list)
            t.append_sequence_items(new_list, current)
            continue

        # --- fallback ---
        t.assign(current)

    return t.result


def post_deserialize(obj: Any) -> Any:
    return obj
