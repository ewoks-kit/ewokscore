from copy import deepcopy
from typing import Any
from typing import Optional

import numpy
import pytest

from ..._serialization import common
from ..._serialization.common import types
from .example_data.compare_json import assert_deserialized_data


def test_primitives():
    assert _roundtrip(None) is None
    assert _roundtrip("hello") == "hello"
    assert _roundtrip(True) is True
    assert _roundtrip(42) == 42
    assert _roundtrip(3.14) == 3.14


def test_complex():
    val = 1 + 2j
    result = _roundtrip(val)
    assert isinstance(result, complex)
    assert result == val


def test_numpy_int():
    expected = {"data": 5, "__ewoks_serialize__": _SERIALIZE_INFO}

    val = numpy.int64(5)
    assert _pre_serialize(val) == expected

    val = numpy.uintp(5)
    assert _pre_serialize(val) == expected


def test_numpy_float():
    expected = {"data": 3.5, "__ewoks_serialize__": _SERIALIZE_INFO}

    val = numpy.float64(3.5)
    assert _pre_serialize(val) == expected

    try:
        val = numpy.float128(1e10)
    except AttributeError:
        pass
    else:
        expected = {"data": 1e10, "__ewoks_serialize__": _SERIALIZE_INFO}
        assert _pre_serialize(val) == expected


def test_numpy_complex():
    obj = numpy.complex64(1 + 2j)
    result = _roundtrip(obj)
    assert isinstance(result, numpy.complex64)
    assert result == obj


def test_numpy_array():
    obj = numpy.array([1, 2])
    result = _roundtrip(obj)
    assert isinstance(result, numpy.ndarray)
    assert result.tolist() == obj.tolist()


def test_list():
    obj = [1, 2, 3]
    assert _roundtrip(obj) == obj


def test_dict():
    obj = {"a": 1, "b": 2}
    assert _roundtrip(obj) == obj


def test_nested():
    obj = {"a": [1, {"b": (2, 3)}]}
    assert _roundtrip(obj) == obj


def test_tuple():
    obj = (1, 2, 3)
    result = _roundtrip(obj)
    assert isinstance(result, tuple)
    assert result == obj


def test_set():
    obj = {1, 2, 3}
    result = _roundtrip(obj)
    assert isinstance(result, set)
    assert result == obj


def test_bytes():
    obj = b"hello"
    result = _roundtrip(obj)
    assert isinstance(result, bytes)
    assert result == obj


class Custom:
    def __init__(self, x):
        self.x = x

    def __eq__(self, other):
        return isinstance(other, Custom) and self.x == other.x


def test_pickle_fallback():
    obj = Custom(10)
    result = _roundtrip(obj)
    assert isinstance(result, Custom)
    assert result == obj


def test_special_rules():
    obj = {"links": [{"source": 1}, {"other": 2}]}

    def encode(v):
        return f"encoded:{v}"

    def decode(v):
        return int(v.split(":")[1])

    encoders = {
        ("links", "*", "source"): encode,
    }

    decoders = {
        ("data", "links", "*", "source"): decode,
    }

    original = deepcopy(obj)
    result = _pre_serialize(obj, item_serializers=encoders)
    assert obj == original

    expected = {
        "data": {"links": [{"source": "encoded:1"}, {"other": 2}]},
        "__ewoks_serialize__": _SERIALIZE_INFO,
    }
    assert result == expected

    original = deepcopy(result)
    result2 = _post_deserialize(result, item_deserializers=decoders)
    assert result == original

    expected = {
        "data": {"links": [{"source": 1}, {"other": 2}]},
        "__ewoks_serialize__": _SERIALIZE_INFO,
    }
    assert result2 == expected


def test_reserved_key_error():
    obj = {"__ewoks__": "bad"}
    with pytest.raises(types.EwoksEncodeError):
        _pre_serialize(obj)


def test_unknown_tag():
    obj = {"data": {"__ewoks__": "unknown"}, "__ewoks_serialize__": _SERIALIZE_INFO}
    with pytest.raises(types.EwoksDecodeError):
        _post_deserialize(obj)


def test_no_max_recursion_exeception():
    depth = 10000
    obj = current = {}
    for _ in range(depth):
        new = {}
        current["x"] = new
        current = new

    result = _roundtrip(obj, check_modified=False)
    assert isinstance(result, dict)


def test_complex_structure():
    obj = {
        "a": [1, 2, (3, 4)],
        "b": {5, 6},
        "c": b"bytes",
        "d": {"nested": numpy.int64(7)},
    }
    assert _roundtrip(obj) == obj


_SERIALIZE_INFO = dict(serializer="json_pickle", serializer_version="1.0.0")


def _pre_serialize(obj: Any, **kwargs) -> Any:
    return common.pre_serialize(
        obj,
        serializer="json_pickle",
        insert_serialize_info=_insert_serialize_info,
        **kwargs,
    )


def _post_deserialize(obj: Any, **kwargs) -> Any:
    return common.post_deserialize(
        obj, pop_serialize_info=_pop_serialize_info, **kwargs
    )


def _insert_serialize_info(
    data: Any, key: str, serialize_info: types.SerializeInfo
) -> dict:
    return {"data": data, key: serialize_info.serialize()}


def _pop_serialize_info(data: dict, key: str) -> Optional[types.SerializeInfo]:
    serialize_info = data.get(key)
    if serialize_info:
        return types.SerializeInfo.deserialize(serialize_info)


def _roundtrip(obj: Any, check_modified: bool = True) -> Any:
    if check_modified:
        original = deepcopy(obj)

    ser_obj = _pre_serialize(obj)

    if check_modified:
        assert_deserialized_data(obj, original)

    return _post_deserialize(ser_obj)["data"]
