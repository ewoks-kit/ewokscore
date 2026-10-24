from pydantic import BaseModel

from ...model import BaseOutputModel


class RangeInfo(BaseOutputModel):
    extent: float
    minimum: float
    maximum: float


def range_info(a: float, b: float) -> RangeInfo:
    """Information on the range between two numbers."""
    return RangeInfo(extent=abs(b - a), minimum=min(a, b), maximum=max(a, b))


class PlainModel(BaseModel):
    total: int


def plain_model_method(a: int, b: int = 1) -> PlainModel:
    return PlainModel(total=a + b)
