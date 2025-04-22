from typing import Any

try:
    from typing import Annotated, get_args
except ImportError:
    # python <3.9
    from typing_extensions import Annotated, get_args

from pydantic import BaseModel, WrapValidator
from pydantic.annotated_handlers import GetCoreSchemaHandler

from .variable import Variable
from .hashing import HasUhash
from .hashing import UniversalHash
from .persistence.proxy import DataUri
from .persistence.proxy import DataProxy


class BaseInputModel(BaseModel, arbitrary_types_allowed=True):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)

        rebuild = False
        for field in cls.model_fields.values():
            if _IgnoresVariableWrapperTypes in get_args(field.annotation):
                continue
            field.annotation = Annotated[
                field.annotation,
                WrapValidator(_ignore_variable_wrapper_types),
                _IgnoresVariableWrapperTypes,
            ]
            rebuild = True

        if rebuild:
            cls.model_rebuild(force=True)


class _IgnoresVariableWrapperTypes:
    pass


_VARIABLE_WRAPPER_TYPES = Variable, UniversalHash, HasUhash, DataProxy, DataUri


def _ignore_variable_wrapper_types(value: Any, handler: GetCoreSchemaHandler) -> Any:
    if isinstance(value, _VARIABLE_WRAPPER_TYPES):
        return value
    return handler(value)
