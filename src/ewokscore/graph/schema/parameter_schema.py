import sys
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Union

from jsonschema import Draft202012Validator
from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self


class _Target(BaseModel):
    name: str
    id: Union[str, int, None] = None
    label: Optional[str] = None
    task_identifier: Optional[str] = None
    all: bool = False


class _Property(BaseModel, extra="allow"):
    x_ewoks_targets: List[_Target] = Field(default_factory=list)


class EwoksParameterSchema(BaseModel, extra="forbid"):
    schema_url: Literal["https://json-schema.org/draft/2020-12/schema"] = Field(
        default="https://json-schema.org/draft/2020-12/schema",
        alias="$schema",
    )

    type: Literal["object"] = "object"

    properties: Dict[str, _Property]
    required: List[str] = Field(default_factory=list)

    additionalProperties: Literal[False] = False

    @model_validator(mode="after")
    def validate_json_schema(self) -> Self:
        schema_dict = self.model_dump(by_alias=True)

        # validates that the structure is a valid JSON Schema
        Draft202012Validator.check_schema(schema_dict)

        return self

    @model_validator(mode="after")
    def validate_required(self) -> Self:
        missing = set(self.required) - self.properties.keys()
        if missing:
            raise ValueError(
                f"'required' contains unknown properties: {sorted(missing)}"
            )
        return self
