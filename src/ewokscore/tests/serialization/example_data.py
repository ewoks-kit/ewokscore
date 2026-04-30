from typing import Any
from typing import Dict

import numpy


def generate_example_data() -> Dict[str, Any]:
    value = {
        "string": "string",
        "bytes": b"bytes",
        "int": 42,
        "float": 20.3,
        "np_scalar1": numpy.uint16(10),
        "np_scalar2": numpy.float64(-10),
        "empty_list": [],
        "empty_tuple": (),
        "empty_set": {},
        "list": [-1, -2, -3],
        "tuple": (1, 2, 3),
        "nested_tuple": ("a", ("b", "c")),
        "set": {100, 200, 300},
        "np_array": numpy.array([10, 20, 30]),
        "custom_type": _CustomType(42),
    }
    try:
        value["np_scalar3"] = numpy.float128(1e10)
    except AttributeError:
        pass
    return {
        **value,
        "nested_list": [value],
        "nested_tuple": (value,),
        "nested_set": {(1, 2), (3, 4)},
        "nested_dict": {"value": value},
    }


class _CustomType:
    def __init__(self, value):
        self._value = value

    def __eq__(self, value):
        return isinstance(value, _CustomType) and value._value == self._value


def assert_python_data(python_data: Dict[str, Any], original_data: Dict[str, Any]):
    actual = _data_for_python_comparison(python_data)
    expected = _data_for_python_comparison(original_data)
    assert actual == expected


def assert_raw_data(raw_data: Dict[str, Any], original_data: Dict[str, Any]):
    actual = _actual_data_for_raw_comparison(raw_data)
    expected = _expected_data_for_raw_comparison(original_data)
    assert actual == expected


def _data_for_python_comparison(value: Any) -> Any:
    if isinstance(value, numpy.ndarray):
        return {
            "__test_compare__": True,
            "__type__": value.dtype,
            "__values__": value.tolist(),
        }
    if isinstance(value, dict):
        return {k: _data_for_python_comparison(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return type(value)(_data_for_python_comparison(v) for v in value)
    return value


def _actual_data_for_raw_comparison(raw_data: Any) -> Any:
    if isinstance(raw_data, dict):
        if "__ewoks__" in raw_data:
            return {"__test_compare__": raw_data["__ewoks__"]}
        return {k: _actual_data_for_raw_comparison(v) for k, v in raw_data.items()}
    if isinstance(raw_data, list):
        return list(_actual_data_for_raw_comparison(v) for v in raw_data)
    return raw_data


def _expected_data_for_raw_comparison(original_data: Any) -> Any:
    if isinstance(original_data, (bytes, tuple, set)):
        return {"__test_compare__": type(original_data).__name__}
    if isinstance(original_data, (numpy.ndarray, _CustomType)):
        return {"__test_compare__": "pickle"}
    if isinstance(original_data, dict):
        return {
            "__ewoks__:" + ":".join(map(str, k))
            if isinstance(k, tuple)
            else k: _expected_data_for_raw_comparison(v)
            for k, v in original_data.items()
        }
    if isinstance(original_data, list):
        return list(_expected_data_for_raw_comparison(v) for v in original_data)
    return original_data
