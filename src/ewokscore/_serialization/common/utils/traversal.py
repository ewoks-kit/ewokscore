from typing import Any
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

from . import types

_StackItemType = Tuple[
    Optional[types.ContainerType], Optional[types.KeyType], Any, types.Path
]


class Traversal:
    def __init__(self, root: Any):
        self._stack: List[_StackItemType] = [(None, None, root, ())]

        self._parent: Optional[types.ContainerType] = None
        self._key: Optional[types.KeyType] = None
        self._current: Any = None
        self._path: types.Path = ()

        self._result: Any = None

    @property
    def result(self) -> Any:
        return self._result

    @property
    def parent(self) -> Optional[types.ContainerType]:
        return self._parent

    @property
    def key(self) -> Optional[types.KeyType]:
        return self._key

    @property
    def current(self) -> Any:
        return self._current

    @property
    def path(self) -> types.Path:
        return self._path

    def next(self) -> bool:
        if not self._stack:
            return False
        self._parent, self._key, self._current, self._path = self._stack.pop()
        return True

    def assign(self, value: Any) -> None:
        if self._parent is None:
            self._result = value
        else:
            self._parent[self._key] = value

    def append_dict_key(
        self,
        parent: Optional[types.ContainerType],
        key: Optional[types.KeyType],
        value: Any,
    ) -> None:
        self._stack.append((parent, key, value, self._path + (key,)))

    def append_sequence_items(self, parent: Any, items: Sequence) -> None:
        for key in reversed(range(len(items))):
            self._stack.append((parent, key, items[key], self._path + (key,)))
