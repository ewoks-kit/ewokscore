from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

from . import types

# Container to assign to, key in that container, value to visit, traversal state
_StackItemType = Tuple[Optional[types.ContainerType], Optional[types.KeyType], Any, Any]


class Traversal:
    """Rebuild a nested structure of dictionaries and sequences, one value at a time.

    Pop the next value with `next`, then either `assign` what it becomes in the
    result, or rebuild its container with `assign_dict`/`assign_sequence` which
    pushes its children to be visited later. Once `next` returns `False` the
    rebuilt structure is available as `result`.

    .. code-block:: python

        t = Traversal(obj)
        while t.next():
            current = t.current
            if isinstance(current, dict):
                t.assign_dict(current)
            elif isinstance(current, list):
                t.assign_sequence(current)
            else:
                t.assign(transform(current))
        return t.result

    Nothing recurses, so the depth of the structure is not limited by the Python
    recursion limit.
    """

    __slots__ = ("_stack", "_parent", "_key", "_current", "_state", "_result")

    def __init__(self, root: Any, state: Any = None) -> None:
        self._stack: List[_StackItemType] = [(None, None, root, state)]

        self._parent: Optional[types.ContainerType] = None
        self._key: Optional[types.KeyType] = None
        self._current: Any = None
        self._state: Any = None

        self._result: Any = None

    @property
    def result(self) -> Any:
        """The rebuilt structure, complete once `next` returned `False`."""
        return self._result

    @property
    def parent(self) -> Optional[types.ContainerType]:
        """The container the current value is assigned to, `None` for the root."""
        return self._parent

    @property
    def key(self) -> Optional[types.KeyType]:
        """The key of the current value in `parent`, `None` for the root."""
        return self._key

    @property
    def current(self) -> Any:
        """The value being visited."""
        return self._current

    @property
    def state(self) -> Any:
        """Whatever was pushed along with the current value.

        For traversals that need to know where in the structure they are, without
        paying for bookkeeping the others do not need.
        """
        return self._state

    def next(self) -> bool:
        """Move to the next value to visit. `False` when nothing is left."""
        if not self._stack:
            return False
        self._parent, self._key, self._current, self._state = self._stack.pop()
        return True

    def assign(self, value: Any) -> None:
        """Set what the current value becomes in the result."""
        if self._parent is None:
            self._result = value
        else:
            self._parent[self._key] = value

    def append(
        self,
        parent: Optional[types.ContainerType],
        key: Optional[types.KeyType],
        value: Any,
        state: Any = None,
    ) -> None:
        """Push a value to visit later and assign to `parent[key]`."""
        self._stack.append((parent, key, value, state))

    def append_sequence(self, parent: Any, items: Iterable) -> None:
        """Push all items of `items`, to be assigned to `parent` by index.

        Items that cannot be indexed, a set for example, are materialized first.
        """
        if not isinstance(items, (list, tuple)):
            items = list(items)
        stack = self._stack
        for key in reversed(range(len(items))):
            stack.append((parent, key, items[key], None))

    def assign_dict(
        self,
        current: Dict[Any, Any],
        key_converter: Optional[Callable[[Any], types.KeyType]] = None,
    ) -> Dict[types.KeyType, Any]:
        """Rebuild the current dictionary and push all its values.

        Pushed in reverse order, so that popping them restores the key order of
        `current`.
        """
        new_dict: Dict[types.KeyType, Any] = dict()
        self.assign(new_dict)
        stack = self._stack
        for key, value in reversed(list(current.items())):
            if key_converter is not None:
                key = key_converter(key)
            stack.append((new_dict, key, value, None))
        return new_dict

    def assign_sequence(self, items: Sequence) -> List[Any]:
        """Rebuild the current sequence as a list and push all its items."""
        new_list: List[Any] = [None] * len(items)
        self.assign(new_list)
        self.append_sequence(new_list, items)
        return new_list
