from typing import Any
from pathlib import Path
import json

from .file import FileProxy
from .atomic import atomic_write


class JsonProxy(FileProxy):
    """Example root URI's:
    * "file://path/to/directory"
    * "file://path/to/file.json"
    """

    SCHEME = "json"
    EXTENSION = ".json"

    def _dump(self, path: Path, data: Any):
        with atomic_write(path) as f:
            json.dump(data, f)

    def _load(self, path: Path):
        with open(path, mode="r") as f:
            return json.load(f)
