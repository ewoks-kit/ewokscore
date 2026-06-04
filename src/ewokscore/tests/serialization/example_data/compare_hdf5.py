from typing import Any
from typing import Dict

import numpy

from ...._serialization.common.hdf5_pickle import _is_scalar_sequence
from .types import CustomType


def assert_deserialized_data(
    deserialized_data: Dict[str, Any], original_data: Dict[str, Any]
):
    actual = _data_for_comparison(_remove_hdf5_attrs(deserialized_data))
    expected = _data_for_comparison(original_data)

    assert actual == expected


def assert_serialized_data(
    serialized_data: Dict[str, Any], original_data: Dict[str, Any]
):
    actual = _actual_data_for_serialized_comparison(serialized_data)
    expected = _expected_data_for_serialized_comparison(original_data)

    assert actual == expected


def _remove_hdf5_attrs(deserialized_data: dict) -> None:
    return {
        k: _remove_hdf5_attrs(v) if isinstance(v, dict) else v
        for k, v in deserialized_data.items()
        if k not in ("@NX_class",)
    }


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
    :param serialized_data: data read directly from HDF5 without deserialization
    """
    if isinstance(serialized_data, dict):
        if "__ewoks__" in serialized_data:
            return {"__test_compare__": serialized_data["__ewoks__"].item()}
        return {
            k: _actual_data_for_serialized_comparison(v)
            for k, v in serialized_data.items()
        }
    if isinstance(serialized_data, list):
        return list(_actual_data_for_serialized_comparison(v) for v in serialized_data)
    if isinstance(serialized_data, numpy.ndarray):
        if serialized_data.ndim == 0:
            return serialized_data.item()
        return {
            "__test_compare__": True,
            "__type__": serialized_data.dtype,
            "__values__": serialized_data.tolist(),
        }
    return serialized_data


def _expected_data_for_serialized_comparison(original_data: Any) -> Any:
    """
    :param original_data: original python data before serialization
    """
    if isinstance(original_data, (list, tuple, set)) and _is_scalar_sequence(
        original_data
    ):
        return {"__test_compare__": type(original_data).__name__}
    if isinstance(original_data, (bytes,)):
        return {"__test_compare__": type(original_data).__name__}
    if isinstance(original_data, (tuple, set, list, CustomType)):
        return {"__test_compare__": "pickle"}
    if isinstance(original_data, dict):
        return {
            k: _expected_data_for_serialized_comparison(v)
            for k, v in original_data.items()
        }
    if isinstance(original_data, numpy.ndarray):
        if original_data.ndim == 0:
            return original_data.item()
        return {
            "__test_compare__": True,
            "__type__": original_data.dtype,
            "__values__": original_data.tolist(),
        }
    return original_data
