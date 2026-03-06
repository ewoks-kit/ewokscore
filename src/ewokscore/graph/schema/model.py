from typing import Any
from typing import Hashable
from typing import Literal
from typing import Optional
from typing import Sequence
from typing import Union

from pydantic import BaseModel

NodeId = Hashable  # Could be recursive: Union[Tuple[str, "Id"], str]


class EwoksDataMapping(BaseModel):
    source_output: Optional[NodeId] = None
    target_input: NodeId


class EwoksCondition(BaseModel):
    source_output: NodeId
    value: Any


class EwoksInput(BaseModel):
    name: Union[str, int]
    value: Any


class EwoksNodeAttributes(BaseModel):
    default_inputs: Optional[Sequence[EwoksInput]] = None
    force_start_node: bool = False
    conditions_else_value: bool = False
    default_error_node: bool = False
    default_error_attributes: Optional["EwoksLink"] = None


class EwoksLinkAttributes(BaseModel):
    data_mapping: Sequence[EwoksDataMapping] = []  # Exclusive with `map_all_data`
    map_all_data: bool = False
    conditions: Sequence[EwoksCondition] = []
    on_error: bool = False
    conditional: bool = False
    required: bool = False
    cache_non_required: bool = False


class EwoksLink(EwoksLinkAttributes):
    source: Hashable
    sub_source: Optional[Hashable] = None
    target: Hashable
    sub_target: Optional[Hashable] = None
    sub_target_attributes: Optional[EwoksNodeAttributes] = None


class EwoksNode(EwoksNodeAttributes):
    id: NodeId
    label: Optional[str] = None
    task_identifier: Optional[str] = None  # Only optional for ppfport (TODO)
    task_type: Literal[
        "class",
        "generated",
        "method",
        "graph",
        "ppfmethod",
        "ppfport",
        "script",
        "notebook",
    ]
    task_generator: Optional[str] = None


class EwoksNodeAlias(EwoksNodeAttributes):
    id: NodeId
    node: NodeId
    sub_node: Optional[NodeId] = None
    link_attributes: Optional[EwoksLinkAttributes] = None


class EwoksGraphAttributes(BaseModel):
    id: str
    label: Optional[str] = None
    schema_version: str = "1.1"  # SHOULD BE LATEST
    requirements: Sequence[str] = []
    input_nodes: Sequence[EwoksNodeAlias] = []
    output_nodes: Sequence[EwoksNodeAlias] = []


class EwoksGraph(BaseModel):
    graph: EwoksGraphAttributes
    nodes: Sequence[EwoksNode] = []
    links: Sequence[EwoksLink] = []
