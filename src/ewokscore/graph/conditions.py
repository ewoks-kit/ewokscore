import operator
from typing import Any
from typing import Tuple

from ..node import NodeIdType


def _in(actual: Any, expected_values: Any) -> bool:
    return actual in expected_values


def _not_in(actual: Any, expected_values: Any) -> bool:
    return actual not in expected_values


CONDITION_OPERATORS = {
    "eq": operator.eq,
    "ne": operator.ne,
    "lt": operator.lt,
    "le": operator.le,
    "gt": operator.gt,
    "ge": operator.ge,
    "in": _in,
    "not_in": _not_in,
}

CONDITION_OPERATOR_NAMES = tuple(CONDITION_OPERATORS)
CONDITION_COLLECTION_OPERATOR_NAMES = ("in", "not_in")
DEFAULT_CONDITION_OPERATOR = "eq"
COMPLEMENTARY_CONDITION_OPERATORS = {
    "eq": "ne",
    "ne": "eq",
    "lt": "ge",
    "ge": "lt",
    "le": "gt",
    "gt": "le",
    "in": "not_in",
    "not_in": "in",
}


def normalize_condition(condition: dict) -> Tuple[NodeIdType, str, Any]:
    return (
        condition["source_output"],
        condition.get("operator", DEFAULT_CONDITION_OPERATOR),
        condition["value"],
    )


def is_condition_collection_value(value: Any) -> bool:
    return isinstance(value, (list, tuple, set))


def condition_values_equal(value1: Any, value2: Any) -> bool:
    return value1 == value2


def condition_value_for_set(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, set):
        return frozenset(value)
    return value
