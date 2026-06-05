from pathlib import Path
from typing import Any
from typing import Mapping
from typing import MutableMapping
from typing import Optional
from typing import Union

from .._serialization import json
from .._serialization.common import types
from . import atomic
from .file import FileProxy


def modify_dict(target: Mapping, source: MutableMapping):
    for name, value in source.items():
        if isinstance(value, dict):
            new_target = target.setdefault(name, dict())
            modify_dict(new_target, value)
        else:
            target[name] = value


class JsonProxy(FileProxy):
    SCHEME = "json"
    EXTENSIONS = [".json"]
    ALLOW_PATH_IN_FILE = False

    def _dump(
        self,
        path: Path,
        data: Any,
        serializer: Optional[
            Union[types.GraphSerializer, str]
        ] = types.GraphSerializer.json_pickle,
        **kwargs,
    ):
        with atomic.atomic_write(path, mode="w") as f:
            json.dump(
                data,
                f,
                serializer=serializer,
                insert_serialize_info=_insert_serialize_info,
                **kwargs,
            )

    def _load(self, path: Path):
        with open(path, mode="r") as f:
            content = json.load(f, pop_serialize_info=_pop_serialize_info)
            return content["data"]


def _insert_serialize_info(
    data: Any, key: str, serialize_info: types.SerializeInfo
) -> dict:
    return {"data": data, key: serialize_info.serialize()}


def _pop_serialize_info(data: dict, key: str) -> Optional[types.SerializeInfo]:
    serialize_info = data.pop(key, None)
    if serialize_info:
        return types.SerializeInfo.deserialize(serialize_info)
