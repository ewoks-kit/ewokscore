from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from typing import Optional
from typing import Union

from networkx import Graph

from ..models import NodeIdType
from ..models import NodePort

GraphSource = Union[str, Path, Mapping, Graph]


@dataclass
class GraphInput(NodePort):
    id: NodeIdType
    label: Optional[str]
    task_identifier: str
    import_error: Optional[Exception]
