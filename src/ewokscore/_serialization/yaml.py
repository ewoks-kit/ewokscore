from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import TextIO
from typing import Union

import yaml

from . import common
from .common import types


def dumps(
    obj: Any,
    item_serializers: Optional[Dict[types.Path, types.ConverterType]] = None,
    serializer: Optional[Union[types.GraphSerializer, str]] = None,
    insert_serialize_info: Optional[
        Callable[[Any, str, types.SerializeInfo], Any]
    ] = None,
    **kwargs,
) -> str:
    """
    Serialize Python object to YAML string.
    """
    pre = common.pre_serialize(
        obj,
        item_serializers=item_serializers,
        serializer=serializer,
        insert_serialize_info=insert_serialize_info,
    )
    return yaml.dump(pre, stream=None, Dumper=yaml.SafeDumper, **kwargs)


def dump(
    obj: Any,
    fp: TextIO,
    item_serializers: Optional[Dict[types.Path, types.ConverterType]] = None,
    serializer: Optional[Union[types.GraphSerializer, str]] = None,
    insert_serialize_info: Optional[
        Callable[[Any, str, types.SerializeInfo], Any]
    ] = None,
    **kwargs,
) -> None:
    """
    Write Python object to YAML file-like object.
    """
    pre = common.pre_serialize(
        obj,
        item_serializers=item_serializers,
        serializer=serializer,
        insert_serialize_info=insert_serialize_info,
    )
    yaml.dump(pre, stream=fp, Dumper=yaml.SafeDumper, **kwargs)


def loads(
    s: str,
    item_deserializers: Optional[Dict[types.Path, types.ConverterType]] = None,
    pop_serialize_info: Optional[
        Callable[[Any, str], Optional[types.SerializeInfo]]
    ] = None,
    **kwargs,
) -> Any:
    """
    Deserialize YAML string to Python object.
    """
    try:
        raw = yaml.load(s, yaml.Loader, **kwargs)
    except (yaml.YAMLError, TypeError) as e:
        raise types.EwoksDecodeError from e

    return common.post_deserialize(
        raw,
        item_deserializers=item_deserializers,
        pop_serialize_info=pop_serialize_info,
    )


def load(
    fp: TextIO,
    item_deserializers: Optional[Dict[types.Path, types.ConverterType]] = None,
    pop_serialize_info: Optional[
        Callable[[Any, str], Optional[types.SerializeInfo]]
    ] = None,
    **kwargs,
) -> Any:
    """
    Load Python object from YAML file-like object.
    """
    try:
        raw = yaml.load(fp, yaml.Loader, **kwargs)
    except (yaml.YAMLError, TypeError) as e:
        raise types.EwoksDecodeError from e

    return common.post_deserialize(
        raw,
        item_deserializers=item_deserializers,
        pop_serialize_info=pop_serialize_info,
    )
