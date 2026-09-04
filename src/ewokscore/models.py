from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from .missing_data import is_missing_data

NodeIdType = Union[str, int, tuple]
JsonNodeIdType = Union[int, str, list]


class EwoksTaskTypeError(TypeError):
    pass


@dataclass
class NodePort:
    name: str
    value: Any
    required: Optional[bool]
    description: Optional[str]
    examples: Optional[List[Any]]

    @property
    def has_value(self) -> bool:
        return not is_missing_data(self.value)

    @property
    def required_without_value(self) -> bool:
        return bool(self.required) and not self.has_value


@dataclass
class NodeSignature:
    id: NodeIdType
    label: Optional[str]
    task_identifier: str
    import_error: Optional[Exception]
    inputs: List[NodePort]
    outputs: List[NodePort]


class NodeSignatureWithConnections(NodeSignature):
    connections: List[Tuple[str, str]]
