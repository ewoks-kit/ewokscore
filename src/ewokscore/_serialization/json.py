import json
from typing import Any
from typing import List
from typing import Optional
from typing import TextIO

from . import common


def dumps(
    obj: Any, custom_rules: Optional[List[common.RuleType]] = None, **kwargs
) -> str:
    """
    Serialize Python object to JSON string.
    """
    pre = common.pre_serialize(obj, custom_rules=custom_rules)
    return json.dumps(pre, **kwargs)


def dump(
    obj: Any,
    fp: TextIO,
    custom_rules: Optional[List[common.RuleType]] = None,
    **kwargs,
) -> None:
    """
    Write Python object to JSON file-like object.
    """
    pre = common.pre_serialize(obj, custom_rules=custom_rules)
    json.dump(pre, fp, **kwargs)


def loads(
    s: str, custom_rules: Optional[List[common.RuleType]] = None, **kwargs
) -> Any:
    """
    Deserialize JSON string to Python object.
    """
    try:
        raw = json.loads(s, **kwargs)
    except (json.JSONDecodeError, TypeError) as e:
        raise common.EwoksDecodeError from e

    return common.post_deserialize(raw, custom_rules=custom_rules)


def load(
    fp: TextIO, custom_rules: Optional[List[common.RuleType]] = None, **kwargs
) -> Any:
    """
    Load Python object from JSON file-like object.
    """
    try:
        raw = json.load(fp, **kwargs)
    except (json.JSONDecodeError, TypeError) as e:
        raise common.EwoksDecodeError from e

    return common.post_deserialize(raw, custom_rules=custom_rules)
