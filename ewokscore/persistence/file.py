from typing import List, Optional, Any
from pathlib import Path
from urllib.parse import ParseResult
from .uri import path_from_uri
from . import proxy
from ..hashing import UniversalHashable


class FileProxy(proxy.DataProxy, register=False):
    """Example root URI's:
    * "file://path/to/directory"
    * "file://path/to/name.ext"
    * "file://path/to/name.ext?path=/path/in/file"
    """

    EXTENSIONS = NotImplemented
    ALLOW_PATH_IN_FILE = NotImplemented
    SEP_IN_FILE = "/"

    @property
    def path(self) -> Optional[Path]:
        if self.fixed_uri:
            return path_from_uri(self.uri.parse())
        parsed_root_uri = self.parsed_root_uri
        if parsed_root_uri is None:
            return None
        identifier = self.identifier
        if identifier is None:
            return None

        # Directory or file name
        root_path = path_from_uri(parsed_root_uri)
        extension = root_path.suffix
        path_is_file = bool(extension)
        if extension not in self.EXTENSIONS:
            extension = self.EXTENSIONS[0]
        path = root_path.with_suffix("")

        # Add path-in-file to path when the file format does not support it
        if self.ALLOW_PATH_IN_FILE:  # for example JSON
            add_identifier_to_path = not path_is_file
        else:  # for example HDF5
            subdirs = self._path_in_file_parts()
            if subdirs:
                path = path.joinpath(*subdirs)
                add_identifier_to_path = False
            else:
                add_identifier_to_path = True

        # Add the identifier to the path if needed
        if add_identifier_to_path:
            filename = identifier
            path /= filename

        return path.with_suffix(extension)

    def _path_in_file_parts(self) -> List[str]:
        parts = [s for s in self.root_uri_path_in_file.split(self.SEP_IN_FILE) if s]
        if self.fixed_uri:
            return parts
        identifier = self.identifier
        if identifier is not None:
            parts.append(identifier)
        return parts

    @property
    def root_uri_path_in_file(self) -> str:
        return self.root_uri_query.get("path", "")

    def path_in_file_parts(self) -> Optional[List[str]]:
        if self.ALLOW_PATH_IN_FILE:
            return self._path_in_file_parts()
        else:
            return None

    @property
    def path_in_file(self) -> Optional[str]:
        if self.ALLOW_PATH_IN_FILE:
            return self.SEP_IN_FILE.join(self._path_in_file_parts())
        else:
            return None

    @property
    def path_in_file_parent(self) -> Optional[str]:
        if self.ALLOW_PATH_IN_FILE:
            parts = self._path_in_file_parts()[:-1]
            return self.SEP_IN_FILE.join(parts)
        else:
            return None

    @property
    def path_in_file_name(self) -> Optional[str]:
        if self.ALLOW_PATH_IN_FILE:
            return self._path_in_file_parts()[-1]
        else:
            return None

    def _generate_uri(self) -> Optional[proxy.DataUri]:
        path = self.path
        if path is None:
            return
        query = dict()
        path_in_file = self.path_in_file
        if path_in_file:
            query["path"] = path_in_file
        if query:
            query = "&".join([f"{name}={value}" for name, value in query.items()])
        else:
            query = ""

        uri = ParseResult(self.SCHEME, str(path), "", "", query, "")
        return proxy.DataUri(uri, self.uhash)

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
                raise proxy.PersistenceError(path) from e
        return UniversalHashable.MISSING_DATA

    def _dump(self, path: Path, data: Any) -> None:
        raise NotImplementedError

    def _load(self, path: Path) -> Any:
        raise NotImplementedError
