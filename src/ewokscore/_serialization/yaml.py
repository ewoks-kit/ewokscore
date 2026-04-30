from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import TextIO

import yaml

from . import common


def dumps(
    obj: Any, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> str:
    """
    Serialize Python object to YAML string.
    """
    pre = common.pre_serialize(obj, special_keys=special_keys)
    return yaml.dump(pre, stream=None, Dumper=yaml.Dumper, **kwargs)


def dump(
    obj: Any,
    fp: TextIO,
    special_keys: Optional[Dict[str, Callable[[Any], str]]] = None,
    **kwargs,
) -> None:
    """
    Write Python object to YAML file-like object.
    """
    pre = common.pre_serialize(obj, special_keys=special_keys)
    yaml.dump(pre, stream=fp, Dumper=yaml.Dumper, **kwargs)


def loads(
    s: str, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> Any:
    """
    Deserialize YAML string to Python object.
    """
    try:
        raw = yaml.load(s, yaml.Loader, **kwargs)
    except (yaml.YAMLError, TypeError) as e:
        raise common.EwoksDecodeError from e

    return common.post_deserialize(raw, special_keys=special_keys)


def load(
    fp: TextIO, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> Any:
    """
    Load Python object from YAML file-like object.
    """
    try:
        raw = yaml.load(fp, yaml.Loader, **kwargs)
    except (yaml.YAMLError, TypeError) as e:
        raise common.EwoksDecodeError from e

    return common.post_deserialize(raw, special_keys=special_keys)
