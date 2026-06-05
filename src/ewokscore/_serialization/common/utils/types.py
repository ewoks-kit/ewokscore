from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from typing import Union

try:
    from enum import StrEnum
except ImportError:
    from backports.strenum import StrEnum


class GraphSerializer(StrEnum):
    json = "json"
    json_pickle = "json_pickle"
    hdf5_pickle = "hdf5_pickle"


class SerializeInfo(NamedTuple):
    serializer: Optional[GraphSerializer]
    serializer_version: str

    def serialize(self):
        serializer = str(self.serializer) if self.serializer is not None else None
        return {
            "serializer": serializer,
            "serializer_version": self.serializer_version,
        }

    @classmethod
    def deserialize(cls, serialize_info: dict):
        serializer = serialize_info.get("serializer")
        if serializer is not None:
            serializer = GraphSerializer(serializer)

        serializer_version = serialize_info["serializer_version"]
        return cls(serializer=serializer, serializer_version=serializer_version)


class EwoksEncodeError(ValueError):
    pass


class EwoksDecodeError(ValueError):
    pass


KeyType = Union[str, int]
Path = Tuple[KeyType, ...]
PathPattern = Tuple[KeyType, ...]
ConverterType = Callable[[Any], Any]
ContainerType = Union[Dict[Any, Any], List[Any]]
