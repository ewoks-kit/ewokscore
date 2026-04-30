import numpy as numpy
import pytest

from ..._serialization import common


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
    val = numpy.int64(5)
    assert common.pre_serialize(val) == 5

    val = numpy.uintp(5)
    assert common.pre_serialize(val) == 5


def test_numpy_float():
    val = numpy.float64(3.5)
    assert common.pre_serialize(val) == 3.5

    try:
        val = numpy.float128(1e10)
    except AttributeError:
        pass
    else:
        assert common.pre_serialize(val) == 1e10


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
    assert _roundtrip(obj) == {"a": [1, {"b": (2, 3)}]}


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


def test_special_keys_encode():
    obj = {"x": 1}

    def encode(v):
        return f"encoded:{v}"

    result = common.pre_serialize(obj, special_keys={"x": encode})
    assert result["x"] == "encoded:1"


def test_special_keys_decode():
    obj = {"x": "encoded:1"}

    def decode(v):
        return int(v.split(":")[1])

    result = common.post_deserialize(obj, special_keys={"x": decode})
    assert result["x"] == 1


def test_reserved_key_error():
    obj = {common._EWOKS_KEY: "bad"}
    with pytest.raises(common.EwoksEncodeError):
        common.pre_serialize(obj)


def test_unknown_tag():
    obj = {common._EWOKS_KEY: "unknown"}
    with pytest.raises(common.EwoksDecodeError):
        common.post_deserialize(obj)


def test_deep_nesting():
    depth = 10000
    obj = current = {}
    for _ in range(depth):
        new = {}
        current["x"] = new
        current = new

    result = _roundtrip(obj)
    assert isinstance(result, dict)


def test_complex_structure():
    obj = {
        "a": [1, 2, (3, 4)],
        "b": {5, 6},
        "c": b"bytes",
        "d": {"nested": numpy.int64(7)},
    }

    result = _roundtrip(obj)

    assert result["a"][2] == (3, 4)
    assert result["b"] == {5, 6}
    assert result["c"] == b"bytes"
    assert result["d"]["nested"] == 7


def _roundtrip(obj):
    return common.post_deserialize(common.pre_serialize(obj))
