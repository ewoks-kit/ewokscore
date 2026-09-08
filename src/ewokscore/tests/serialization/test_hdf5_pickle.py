from typing import Any

import numpy

from ..._serialization import common
from ..._serialization.common import types


def test_numpy_bool():
    result = _pre_serialize(numpy.bool_(True))
    assert result is True


def test_none():
    assert _pre_serialize(None) == {"__ewoks__": "none"}
    assert _pre_serialize({"a": None}) == {"a": {"__ewoks__": "none"}}


def test_scalar_sequence():
    assert _pre_serialize([1, 2]) == {"__ewoks__": "list", "items": [1, 2]}
    assert _pre_serialize((1, 2)) == {"__ewoks__": "tuple", "items": [1, 2]}
    assert _pre_serialize([]) == {"__ewoks__": "list", "items": []}


def test_non_scalar_sequence():
    """Sequences that cannot be stored as a single HDF5 dataset without changing
    the type of their items."""
    for obj in (["a", 1], [1, 2.5], [True, 1], [1, None], [[1], [2]], [{"a": 1}]):
        assert _pre_serialize(obj)["__ewoks__"] == "pickle", obj


_SERIALIZE_INFO = dict(serializer="hdf5_pickle", serializer_version="1.0.0")


def _pre_serialize(obj: Any) -> Any:
    result = common.pre_serialize(
        obj, serializer="hdf5_pickle", insert_serialize_info=_insert_serialize_info
    )
    assert result.pop("__ewoks_serialize__") == _SERIALIZE_INFO
    return result["data"]


def _insert_serialize_info(
    data: Any, key: str, serialize_info: types.SerializeInfo
) -> dict:
    return {"data": data, key: serialize_info.serialize()}
