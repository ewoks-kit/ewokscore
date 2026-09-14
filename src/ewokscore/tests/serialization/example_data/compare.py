from typing import Any
from typing import Dict
from typing import Tuple

import numpy

from ...._serialization.common.hdf5_pickle import _is_scalar_sequence
from .types import CustomType


def assert_deserialized_data(
    deserialized_data: Dict[str, Any], original_data: Dict[str, Any]
):
    actual = _data_for_comparison(deserialized_data)
    expected = _data_for_comparison(original_data, original=True)
    assert actual == expected


def assert_json_serialized_data(
    serialized_data: Dict[str, Any], original_data: Dict[str, Any]
):
    actual = _actual_json_data(serialized_data)
    expected = _expected_json_data(original_data)
    assert actual == expected


def assert_hdf5_serialized_data(
    serialized_data: Dict[str, Any], original_data: Dict[str, Any]
):
    actual = _actual_hdf5_data(serialized_data)
    expected = _expected_hdf5_data(original_data)
    assert actual == expected


class _Scalar:
    """Scalar to be compared with its type because storage can silently change it
    (e.g. `int` to `float`)."""

    def __init__(self, value: Any) -> None:
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, _RestoredScalar):
            # the original data dictates which types are allowed
            return other == self
        if not isinstance(other, _Scalar):
            return NotImplemented
        return type(self.value) is type(other.value) and self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"{type(self.value).__name__}({self.value!r})"


class _RestoredScalar(_Scalar):
    """Numpy scalar in the original data, to be compared with the python scalar
    it is restored as."""

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, _Scalar):
            return NotImplemented
        return (
            type(other.value) in _restored_scalar_types(self.value)
            and other.value == self.value
        )

    __hash__ = _Scalar.__hash__


def _restored_scalar_types(value: numpy.generic) -> Tuple[type, ...]:
    """Types a numpy scalar can be restored as: the equivalent python scalar when
    stored as a scalar, the numpy type itself when pickled."""
    if isinstance(value, numpy.bool_):
        return bool, numpy.bool_
    if isinstance(value, (numpy.integer, numpy.floating)):
        # an integral float is restored as an `int`
        return int, float, type(value)
    return type(_python_scalar(value)), type(value)


def _data_for_comparison(value: Any, original: bool = False) -> Any:
    """
    :param original: the data has not been through storage
    """
    if isinstance(value, numpy.ndarray):
        return _array_for_comparison(value)
    if isinstance(value, dict):
        return {k: _data_for_comparison(v, original) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return type(value)(_data_for_comparison(v, original) for v in value)
    if original and isinstance(value, numpy.generic):
        return _RestoredScalar(value)
    return _Scalar(value)


def _scalar_for_comparison(value: Any) -> _Scalar:
    """A numpy scalar is stored as the python scalar with the same value, an
    integral float as an `int` (e.g. `numpy.float64(-10)` is stored as `-10`)."""
    if isinstance(value, numpy.generic):
        scalar = _python_scalar(value)
        if isinstance(scalar, float) and scalar.is_integer():
            return _Scalar(int(scalar))
        return _Scalar(scalar)
    return _Scalar(value)


def _stored_scalar_for_comparison(value: Any) -> _Scalar:
    """HDF5 returns stored scalars as numpy scalars."""
    if isinstance(value, numpy.generic):
        return _Scalar(_python_scalar(value))
    return _Scalar(value)


def _python_scalar(value: numpy.generic) -> Any:
    scalar = value.item()
    if isinstance(scalar, numpy.floating):
        # `numpy.longdouble` has no python equivalent
        return float(scalar)
    return scalar


def _array_for_comparison(value: numpy.ndarray) -> Dict[str, Any]:
    return {
        "__test_compare__": True,
        "__type__": value.dtype,
        "__values__": value.tolist(),
    }


def _actual_json_data(serialized_data: Any) -> Any:
    """
    :param serialized_data: data read directly from JSON without deserialization
    """
    if isinstance(serialized_data, dict):
        if "__ewoks__" in serialized_data:
            return {"__test_compare__": serialized_data["__ewoks__"]}
        return {k: _actual_json_data(v) for k, v in serialized_data.items()}
    if isinstance(serialized_data, list):
        return list(_actual_json_data(v) for v in serialized_data)
    return _stored_scalar_for_comparison(serialized_data)


def _expected_json_data(original_data: Any) -> Any:
    """
    :param original_data: original python data before serialization
    """
    if isinstance(original_data, (bytes, tuple, set)):
        return {"__test_compare__": type(original_data).__name__}
    if isinstance(original_data, (numpy.ndarray, CustomType)):
        return {"__test_compare__": "pickle"}
    if isinstance(original_data, dict):
        return {k: _expected_json_data(v) for k, v in original_data.items()}
    if isinstance(original_data, list):
        return list(_expected_json_data(v) for v in original_data)
    return _scalar_for_comparison(original_data)


def _actual_hdf5_data(serialized_data: Any) -> Any:
    """
    :param serialized_data: data read directly from HDF5 without deserialization
    """
    if isinstance(serialized_data, dict):
        if "__ewoks__" in serialized_data:
            return {"__test_compare__": serialized_data["__ewoks__"].item()}
        return {k: _actual_hdf5_data(v) for k, v in serialized_data.items()}
    if isinstance(serialized_data, list):
        return list(_actual_hdf5_data(v) for v in serialized_data)
    if isinstance(serialized_data, numpy.ndarray):
        if serialized_data.ndim == 0:
            return _stored_scalar_for_comparison(serialized_data.item())
        return _array_for_comparison(serialized_data)
    return _stored_scalar_for_comparison(serialized_data)


def _expected_hdf5_data(original_data: Any) -> Any:
    """
    :param original_data: original python data before serialization
    """
    if original_data is None:
        return {"__test_compare__": "none"}
    if isinstance(original_data, (list, tuple, set)) and _is_scalar_sequence(
        original_data
    ):
        return {"__test_compare__": type(original_data).__name__}
    if isinstance(original_data, bytes):
        return {"__test_compare__": type(original_data).__name__}
    if isinstance(original_data, (tuple, set, list, CustomType)):
        return {"__test_compare__": "pickle"}
    if isinstance(original_data, dict):
        return {k: _expected_hdf5_data(v) for k, v in original_data.items()}
    if isinstance(original_data, numpy.ndarray):
        if original_data.ndim == 0:
            return _scalar_for_comparison(original_data.item())
        return _array_for_comparison(original_data)
    return _scalar_for_comparison(original_data)
