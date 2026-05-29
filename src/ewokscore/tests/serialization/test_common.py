from copy import deepcopy

import numpy
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

    encode_rules = [
        (("links", "*", "source"), encode),
    ]

    decode_rules = [
        (("links", "*", "source"), decode),
    ]

    result = common.pre_serialize(obj, custom_rules=encode_rules)
    assert result["links"][0] == {"source": "encoded:1"}
    assert result["links"][1] == {"other": 2}

    obj2 = common.post_deserialize(result, custom_rules=decode_rules)
    assert obj == obj2


def test_reserved_key_error():
    obj = {common._EWOKS_KEY: "bad"}
    with pytest.raises(common.EwoksEncodeError):
        common.pre_serialize(obj)


def test_unknown_tag():
    obj = {common._EWOKS_KEY: "unknown"}
    with pytest.raises(common.EwoksDecodeError):
        common.post_deserialize(obj)


def test_no_max_recursion_exeception():
    depth = 10000
    obj = current = {}
    for _ in range(depth):
        new = {}
        current["x"] = new
        current = new

    result = _unsaferoundtrip(obj)
    assert isinstance(result, dict)


def test_complex_structure():
    obj = {
        "a": [1, 2, (3, 4)],
        "b": {5, 6},
        "c": b"bytes",
        "d": {"nested": numpy.int64(7)},
    }
    assert _roundtrip(obj) == obj


def _roundtrip(obj):
    return common.post_deserialize(common.pre_serialize(deepcopy(obj)))


def _unsaferoundtrip(obj):
    return common.post_deserialize(common.pre_serialize(obj))
