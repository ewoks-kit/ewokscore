from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import TextIO

import yaml

from . import ewoks_json


def dumps(
    obj: Any, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> str:
    """
    Serialize Python object to YAML string.
    """
    return yaml.dump(ewoks_json.pre_serialize(obj, special_keys=special_keys), **kwargs)


def loads(
    s: str, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> Any:
    """
    Deserialize YAML string to Python object.
    """
    try:
        return ewoks_json.post_deserialize(
            yaml.load(s, yaml.Loader, **kwargs), special_keys=special_keys
        )
    except (yaml.YAMLError, TypeError) as e:
        raise ewoks_json.EwoksDecodeError from e


def dump(
    obj: Any,
    fp: TextIO,
    special_keys: Optional[Dict[str, Callable[[Any], str]]] = None,
    **kwargs,
) -> None:
    """
    Write Python object to YAML file-like object.
    """
    yaml.dump(ewoks_json.pre_serialize(obj, special_keys=special_keys), fp, **kwargs)


def load(
    fp: TextIO, special_keys: Optional[Dict[str, Callable[[Any], str]]] = None, **kwargs
) -> Any:
    """
    Load Python object from YAML file-like object.
    """
    try:
        return ewoks_json.post_deserialize(
            yaml.load(fp, yaml.Loader, **kwargs), special_keys=special_keys
        )
    except (yaml.YAMLError, TypeError) as e:
        raise ewoks_json.EwoksDecodeError from e
