from typing import Union, Any
from pathlib import Path
from .uri import path_from_uri
from . import proxy
from ..hashing import UniversalHashable


class FileProxy(proxy.DataProxy, register=False):
    EXTENSION = NotImplemented

    @property
    def path(self) -> Union[Path, None]:
        if self.fixed_uri:
            return path_from_uri(self.uri.parse())
        if self._root_uri is None:
            return None
        path = path_from_uri(self._root_uri)
        if path.name.endswith(self.EXTENSION):
            return path
        identifier = self._identifier
        if not identifier:
            return None
        filename = identifier + self.EXTENSION
        return path / filename

    def _generate_uri(self) -> Union[None, proxy.DataUri]:
        path = self.path
        if path is None:
            return
        return proxy.DataUri(f"{self.SCHEME}://{self.path}", self.uhash)

    def exists(self) -> bool:
        path = self.path
        if path is None:
            return False
        return path.exists()

    def dump(self, data, **kw):
        path = self.path
        if path is None:
            return False
        self._dump(path, data, **kw)
        return True

    def load(self, raise_error=True, **kw):
        path = self.path
        if path is None:
            return UniversalHashable.MISSING_DATA
        try:
            return self._load(path, **kw)
        except FileNotFoundError as e:
            if raise_error:
                raise proxy.UriNotFoundError(path) from e
        except Exception as e:
            if raise_error:
                raise proxy.PersistencyError(path) from e
        return UniversalHashable.MISSING_DATA

    def _dump(self, path: Path, data: Any) -> None:
        raise NotImplementedError

    def _load(self, path: Path) -> Any:
        raise NotImplementedError
