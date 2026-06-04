"""
Serialization to be executed before the final serialization (JSON, YAML, ...).
"""

from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

from . import explicit
from . import hdf5_pickle
from . import json
from . import json_pickle
from .utils import constants
from .utils import types


def pre_serialize(
    obj: Any,
    item_serializers: Optional[Dict[types.Path, types.ConverterType]] = None,
    serializer: Optional[Union[types.GraphSerializer, str]] = None,
    insert_serialize_info: Optional[
        Callable[[Any, str, types.SerializeInfo], Any]
    ] = None,
) -> Any:
    """
    :param obj: object to serialize
    :param item_serializers: paths to nested dict/list item with associated custom value serialization
    :param serializer: optional serialization
    :param insert_serialize_info: add serializer information to the content
    """
    if serializer is not None and insert_serialize_info is None:
        raise TypeError("'insert_serialize_info' is required")

    serialize_module, serialize_info = _get_serialize_module(serializer)

    obj = explicit.pre_serialize(obj, item_serializers)

    if serialize_module is not None:
        obj = serialize_module.pre_serialize(obj)

    obj = insert_serialize_info(obj, constants.EWOKS_FORMAT_KEY, serialize_info)

    return obj


def post_deserialize(
    obj: Any,
    item_deserializers: Optional[Dict[types.Path, types.ConverterType]] = None,
    pop_serialize_info: Optional[
        Callable[[Any, str], Optional[types.SerializeInfo]]
    ] = None,
) -> Any:
    """
    :param obj: object to deserialize
    :param item_deserializers: paths to nested dict/list item with associated custom value deserialization
    :param pop_serialize_info: get serializer information from the content
    """
    serialize_info = (
        None
        if pop_serialize_info is None
        else pop_serialize_info(obj, constants.EWOKS_FORMAT_KEY)
    )
    if serialize_info is None:
        serialize_module, _ = _get_serialize_module(None)
    else:
        serialize_module, _ = _get_serialize_module(**serialize_info.serialize())

    if serialize_module is not None:
        obj = serialize_module.post_deserialize(obj)

    obj = explicit.post_deserialize(obj, item_deserializers)

    return obj


_CURRENT_VERSION = "1.0.0"
# Applies to all serializers, including the "explicit" serialization which is always used

_OPTIONAL_SERIALIZER_MODULES = {
    (types.GraphSerializer.json, _CURRENT_VERSION): json,
    (types.GraphSerializer.json_pickle, _CURRENT_VERSION): json_pickle,
    (types.GraphSerializer.hdf5_pickle, _CURRENT_VERSION): hdf5_pickle,
}


def _get_serialize_module(
    serializer: Union[types.GraphSerializer, str, None],
    serializer_version: Optional[str] = None,
) -> Tuple[Any, types.SerializeInfo]:
    if serializer_version is None:
        serializer_version = _CURRENT_VERSION
    else:
        if serializer_version != _CURRENT_VERSION:
            raise ValueError(
                f"Ewoks serialization v{serializer_version} is not support. Current version is v{_CURRENT_VERSION}"
            )

    if serializer is None:
        serialize_info = types.SerializeInfo(
            serializer=None, serializer_version=serializer_version
        )
        return None, serialize_info

    if isinstance(serializer, str):
        serializer = types.GraphSerializer(serializer)

    key = serializer, serializer_version
    if key not in _OPTIONAL_SERIALIZER_MODULES:
        raise ValueError(f"No Ewoks serializer found for {key}")
    serialize_module = _OPTIONAL_SERIALIZER_MODULES[key]

    serialize_info = types.SerializeInfo(
        serializer=str(serializer), serializer_version=serializer_version
    )

    return serialize_module, serialize_info
