import json
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import TextIO

from . import common


def dumps(
    obj: Any, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> str:
    """
    Serialize Python object to JSON string.
    """
    pre = common.pre_serialize(obj, special_keys=special_keys)
    return json.dumps(pre, **kwargs)


def dump(
    obj: Any,
    fp: TextIO,
    special_keys: Optional[Dict[str, Callable[[Any], str]]] = None,
    **kwargs,
) -> None:
    """
    Write Python object to JSON file-like object.
    """
    pre = common.pre_serialize(obj, special_keys=special_keys)
    json.dump(pre, fp, **kwargs)


def loads(
    s: str, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> Any:
    """
    Deserialize JSON string to Python object.
    """
    try:
        raw = json.loads(s, **kwargs)
    except (json.JSONDecodeError, TypeError) as e:
        raise common.EwoksDecodeError from e

    return common.post_deserialize(raw, special_keys=special_keys)


def load(
    fp: TextIO, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> Any:
    """
    Load Python object from JSON file-like object.
    """
    try:
        raw = json.load(fp, **kwargs)
    except (json.JSONDecodeError, TypeError) as e:
        raise common.EwoksDecodeError from e

    return common.post_deserialize(raw, special_keys=special_keys)
