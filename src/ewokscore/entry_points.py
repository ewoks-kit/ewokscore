import sys
from typing import Tuple

if sys.version_info < (3, 9):
    from importlib.metadata import EntryPoint

    from importlib_metadata import entry_points as _entry_points

    def entry_points(group: str) -> Tuple[EntryPoint]:
        return tuple(_entry_points(group=group))

elif sys.version_info < (3, 10):
    from importlib.metadata import EntryPoint
    from importlib.metadata import entry_points as _entry_points

    def entry_points(group: str) -> Tuple[EntryPoint]:
        return _entry_points().get(group, ())

else:
    from importlib.metadata import EntryPoint
    from importlib.metadata import entry_points as _entry_points

    def entry_points(group: str) -> Tuple[EntryPoint]:
        return tuple(_entry_points(group=group))
