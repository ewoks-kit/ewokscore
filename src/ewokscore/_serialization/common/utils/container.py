from typing import Any
from typing import Callable


class MutableContainer:
    def __init__(self, mutable: Any, convert: Callable[[Any], Any]):
        self._mutable = mutable
        self._convert = convert

    def get_container(self) -> Any:
        return self._convert(self._mutable)
