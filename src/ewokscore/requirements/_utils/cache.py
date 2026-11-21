import copy
import threading
from typing import Callable
from typing import Dict
from typing import Generic
from typing import Hashable
from typing import TypeVar

_T = TypeVar("_T")


class ProcessCache(Generic[_T]):
    """Values computed once per process.

    Concurrent callers of the same key wait for one computation instead of
    starting their own. Each caller gets a copy of the cached value. A computation
    that raises an exception is not cached.

    The locks only synchronize python threads. They are held while a value is
    computed, so `compute` must not wait for the thread of the caller (e.g. a
    Qt event loop).
    """

    def __init__(self) -> None:
        self._values: Dict[Hashable, _T] = dict()
        self._key_locks: Dict[Hashable, threading.Lock] = dict()
        self._lock = threading.Lock()
        self._generation = 0

    def get(self, key: Hashable, compute: Callable[[], _T]) -> _T:
        with self._lock:
            key_lock = self._key_locks.setdefault(key, threading.Lock())
        with key_lock:
            with self._lock:
                if key in self._values:
                    return copy.deepcopy(self._values[key])
                generation = self._generation
            value = compute()
            with self._lock:
                # Not cached when the cache was cleared during the computation
                if generation == self._generation:
                    self._values[key] = value
            return copy.deepcopy(value)

    def clear(self) -> None:
        with self._lock:
            self._values.clear()
            self._generation += 1
