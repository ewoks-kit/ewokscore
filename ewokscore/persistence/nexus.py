from typing import Union, Any, Tuple
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import ParseResult

from .proxy import DataUri
from .file import FileProxy
from .uri import parse_query
from .atomic import atomic_hdf5
from silx.io.dictdump import dicttonx, nxtodict
from silx.io import h5py_utils


# @h5py_utils.retry(retry_period=1)
def h5_item_exists(path, item):
    with h5py_utils.File(path) as f:
        return item in f


class NexusProxy(FileProxy):
    """Example root URI's:
    * "file://path/to/directory"
    * "file://path/to/file.nx?path=/ewoks_results/"
    """

    SCHEME = "nexus"
    EXTENSION = ".nx"

    @property
    def __parse_result(self) -> ParseResult:
        if self.fixed_uri:
            return self.uri.parse()
        else:
            return self._root_uri

    @property
    def _parent_parts(self) -> list:
        identifier = self._identifier
        if not identifier:
            return list()
        h5_group = parse_query(self.__parse_result).get("path", "")
        parts = [s for s in h5_group.split("/") if s]
        if self.fixed_uri:
            return parts
        nparts = len(parts)
        if nparts == 0:
            parts = ["ewoks_results", identifier]
        elif nparts == 1:
            parts.append(identifier)
        else:
            parts[-1] += "_" + identifier
        return parts

    @property
    def parent(self) -> str:
        return "/".join(self._parent_parts)

    @property
    def name(self) -> str:
        return parse_query(self.__parse_result).get("name", "")

    @property
    def h5_dataset(self) -> Tuple[str, str]:
        h5group = self.parent
        name = self.name
        if name:
            parts = [s for s in name.split("/") if s]
            name = parts[-1]
            subgroup = "/".join(parts[:-1])
            if subgroup:
                h5group += "/" + subgroup
        return h5group, name

    @property
    def h5_path(self) -> str:
        return self.parent + "/" + self.name

    def _generate_uri(self) -> Union[None, DataUri]:
        path = self.path
        if path is None:
            return
        name = self.name
        if name:
            uri = f"{self.SCHEME}://{self.path}?path={self.parent}&name={name}"
        else:
            uri = f"{self.SCHEME}://{self.path}?path={self.parent}"
        return DataUri(uri, self.uhash)

    def exists(self) -> bool:
        if not super().exists():
            return False
        return h5_item_exists(self.path, self.h5_path)

    def _dump(self, path: Path, data: Any, **kw) -> None:
        h5group, name = self.h5_dataset
        if name:
            data = {name: data}
        elif not isinstance(data, Mapping):
            raise TypeError("'data' must be a dictionary")
        else:
            add = {"@NX_class": "NXprocess", "uhash": str(self.uhash)}
            data = {**add, **data}
        kw.setdefault("update_mode", "add")
        kw.setdefault("add_nx_class", True)
        with atomic_hdf5(path, h5group) as (h5file, h5group):
            h5file.attrs["NX_class"] = "NXroot"
            dicttonx(treedict=data, h5file=h5file, h5path=h5group, **kw)
            entry = self._parent_parts[0]
            h5file[entry].attrs["NX_class"] = "NXentry"

    def _load(self, path: Path, **kw) -> Any:
        h5group, name = self.h5_dataset
        adict = nxtodict(h5file=str(path), path=h5group, **kw)
        if name:
            return adict[name]
        return adict
