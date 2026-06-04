from typing import Any
from typing import Dict

import numpy

from .types import CustomType


def assert_deserialized_data(
    deserialized_data: Dict[str, Any], original_data: Dict[str, Any]
):
    actual = _data_for_comparison(deserialized_data)
    expected = _data_for_comparison(original_data)
    assert actual == expected


def assert_serialized_data(
    serialized_data: Dict[str, Any], original_data: Dict[str, Any]
):
    actual = _actual_data_for_serialized_comparison(serialized_data)
    expected = _expected_data_for_serialized_comparison(original_data)
    assert actual == expected


def _data_for_comparison(value: Any) -> Any:
    if isinstance(value, numpy.ndarray):
        return {
            "__test_compare__": True,
            "__type__": value.dtype,
            "__values__": value.tolist(),
        }
    if isinstance(value, dict):
        return {k: _data_for_comparison(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return type(value)(_data_for_comparison(v) for v in value)
    return value


def _actual_data_for_serialized_comparison(serialized_data: Any) -> Any:
    """
    :param serialized_data: data read directly from JSON without deserialization
    """
    if isinstance(serialized_data, dict):
        if "__ewoks__" in serialized_data:
            return {"__test_compare__": serialized_data["__ewoks__"]}
        return {
            k: _actual_data_for_serialized_comparison(v)
            for k, v in serialized_data.items()
        }
    if isinstance(serialized_data, list):
        return list(_actual_data_for_serialized_comparison(v) for v in serialized_data)
    return serialized_data


def _expected_data_for_serialized_comparison(original_data: Any) -> Any:
    """
    :param original_data: original python data before serialization
    """
    if isinstance(original_data, (bytes, tuple, set)):
        return {"__test_compare__": type(original_data).__name__}
    if isinstance(original_data, (numpy.ndarray, CustomType)):
        return {"__test_compare__": "pickle"}
    if isinstance(original_data, dict):
        return {
            k: _expected_data_for_serialized_comparison(v)
            for k, v in original_data.items()
        }
    if isinstance(original_data, list):
        return list(_expected_data_for_serialized_comparison(v) for v in original_data)
    return original_data
