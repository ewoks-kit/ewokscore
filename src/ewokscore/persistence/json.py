import json
import pickle
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import MutableMapping

import numpy

from . import atomic
from .file import FileProxy


def modify_dict(target: Mapping, source: MutableMapping):
    for name, value in source.items():
        if isinstance(value, dict):
            new_target = target.setdefault(name, dict())
            modify_dict(new_target, value)
        else:
            target[name] = value


class EwoksDataTypeJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        if isinstance(obj, (numpy.number, numpy.integer)):
            return obj.item()
        return super().default(obj)
    
class JsonProxy(FileProxy):
    SCHEME = "json"
    EXTENSIONS = [".json"]
    ALLOW_PATH_IN_FILE = False

    def _dump(self, path: Path, data: Any, **_):
        with atomic.atomic_write(path, binary=True) as f:
            json.dump(data, f)
            try:
                # 1. Try JSON with NumPy support
                json_bytes = json.dumps(data, cls=EwoksDataTypeJsonEncoder).encode("utf-8")
                f.write(json_bytes)
            except (TypeError, ValueError):
                # If it's still not serializable, fallback to pickling
                pickle.dump(data, f)

    def _load(self, path: Path):
        with open(path, mode="rb") as f:
            content = f.read()
            if not content:
                return None
            # Pickle files start with the byte \x80
            if content.startswith(b'\x80'):
                return pickle.loads(content)
            return json.loads(content.decode("utf-8"))
