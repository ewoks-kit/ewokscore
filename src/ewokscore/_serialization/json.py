import json
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import TextIO

from . import ewoks_json


def dumps(
    obj: Any, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> str:
    """
    Serialize Python object to JSON string.
    """
    return json.dumps(
        ewoks_json.pre_serialize(obj, special_keys=special_keys), **kwargs
    )


def loads(
    s: str, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> Any:
    """
    Deserialize JSON string to Python object.
    """
    try:
        return ewoks_json.post_deserialize(
            json.loads(s, **kwargs), special_keys=special_keys
        )
    except (json.JSONDecodeError, TypeError) as e:
        raise ewoks_json.EwoksDecodeError from e


def dump(
    obj: Any,
    fp: TextIO,
    special_keys: Optional[Dict[str, Callable[[Any], str]]] = None,
    **kwargs,
) -> None:
    """
    Write Python object to JSON file-like object.
    """
    json.dump(ewoks_json.pre_serialize(obj, special_keys=special_keys), fp, **kwargs)


def load(
    fp: TextIO, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> Any:
    """
    Load Python object from JSON file-like object.
    """
    try:
        return ewoks_json.post_deserialize(
            json.load(fp, **kwargs), special_keys=special_keys
        )
    except (json.JSONDecodeError, TypeError) as e:
        raise ewoks_json.EwoksDecodeError from e
