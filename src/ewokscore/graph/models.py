from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import List
from typing import Mapping
from typing import Optional
from typing import Union

from networkx import Graph

from ..missing_data import is_missing_data
from ..node import NodeIdType

GraphSource = Union[str, Path, Mapping, Graph]


class EwoksTaskTypeError(TypeError):
    pass


@dataclass
class NodeInput:
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
    inputs: List[NodeInput]
    outputs: List[str]


@dataclass
class GraphInput(NodeInput):
    id: NodeIdType
    label: Optional[str]
    task_identifier: str
    import_error: Optional[Exception]
