from typing import Any

from ..._serialization import common
from ..._serialization.common import types


def test_none():
    assert _pre_serialize(None) == {"__ewoks__": "none"}
    assert _pre_serialize({"a": None}) == {"a": {"__ewoks__": "none"}}


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
