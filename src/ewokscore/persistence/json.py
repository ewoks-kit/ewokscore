import base64
import json
import pickle
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import MutableMapping

from . import atomic
from .file import FileProxy


def modify_dict(target: Mapping, source: MutableMapping):
    for name, value in source.items():
        if isinstance(value, dict):
            new_target = target.setdefault(name, dict())
            modify_dict(new_target, value)
        else:
            target[name] = value


class _EwoksJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            return {
                "__pickled__": True,
                "data": base64.b64encode(pickle.dumps(obj)).decode("ascii"),
            }


def _json_pickle_object_hook(obj):
    if isinstance(obj, dict) and obj.get("__pickled__") is True:
        return pickle.loads(base64.b64decode(obj["data"].encode("ascii")))
    return obj


class JsonProxy(FileProxy):
    SCHEME = "json"
    EXTENSIONS = [".json"]
    ALLOW_PATH_IN_FILE = False

    def _dump(self, path: Path, data: Any, **kwargs):
        kwargs.setdefault("cls", _EwoksJsonEncoder)
        with atomic.atomic_write(path, mode="w") as f:
            json.dump(data, f, **kwargs)

    def _load(self, path: Path):
        with open(path, mode="r") as f:
            return json.load(f, object_hook=_json_pickle_object_hook)
