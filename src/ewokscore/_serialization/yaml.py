from typing import Any
from typing import List
from typing import Optional
from typing import TextIO

import yaml

from . import common


def dumps(
    obj: Any, custom_rules: Optional[List[common.RuleType]] = None, **kwargs
) -> str:
    """
    Serialize Python object to YAML string.
    """
    pre = common.pre_serialize(obj, custom_rules=custom_rules)
    return yaml.dump(pre, stream=None, Dumper=yaml.Dumper, **kwargs)


def dump(
    obj: Any,
    fp: TextIO,
    custom_rules: Optional[List[common.RuleType]] = None,
    **kwargs,
) -> None:
    """
    Write Python object to YAML file-like object.
    """
    pre = common.pre_serialize(obj, custom_rules=custom_rules)
    yaml.dump(pre, stream=fp, Dumper=yaml.Dumper, **kwargs)


def loads(
    s: str, custom_rules: Optional[List[common.RuleType]] = None, **kwargs
) -> Any:
    """
    Deserialize YAML string to Python object.
    """
    try:
        raw = yaml.load(s, yaml.Loader, **kwargs)
    except (yaml.YAMLError, TypeError) as e:
        raise common.EwoksDecodeError from e

    return common.post_deserialize(raw, custom_rules=custom_rules)


def load(
    fp: TextIO, custom_rules: Optional[List[common.RuleType]] = None, **kwargs
) -> Any:
    """
    Load Python object from YAML file-like object.
    """
    try:
        raw = yaml.load(fp, yaml.Loader, **kwargs)
    except (yaml.YAMLError, TypeError) as e:
        raise common.EwoksDecodeError from e

    return common.post_deserialize(raw, custom_rules=custom_rules)
