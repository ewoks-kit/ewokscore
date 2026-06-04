from pathlib import Path
from typing import Any
from typing import List
from typing import Mapping
from typing import Optional
from typing import Union

import h5py
from silx.io import h5py_utils
from silx.io.dictdump import dicttonx
from silx.io.dictdump import nxtodict
from silx.utils.proxy import docstring

from .._serialization import common
from .._serialization.common import types
from . import atomic
from .file import FileProxy


# @h5py_utils.retry(retry_period=1)
def h5_item_exists(path, item):
    try:
        with h5py_utils.File(path) as f:
            return item in f
    except Exception:
        return False


class NexusProxy(FileProxy):
    SCHEME = "nexus"
    EXTENSIONS = [".nx", "nxs", ".h5", ".hdf5", ".nexus"]
    ALLOW_PATH_IN_FILE = True

    @docstring(FileProxy)
    def exists(self) -> bool:
        if not super().exists():
            return False
        return h5_item_exists(self.path, self.path_in_file)

    def _dump(
        self,
        path: Path,
        data: Any,
        update_mode: str = "add",
        serializer: Optional[
            Union[types.GraphSerializer, str]
        ] = types.GraphSerializer.hdf5_pickle,
        **_,
    ) -> None:
        prefix = ""
        if isinstance(data, Mapping):
            h5group = self.path_in_file
        else:
            h5group = self.path_in_file_parent
            h5name = self.path_in_file_name
            if h5name:
                data = {h5name: data}
                prefix = h5name
            elif isinstance(data, Mapping):
                pass
            else:
                raise TypeError("'data' must be a dictionary")

        def _insert_serialize_info(
            data: dict, key: str, serialize_info: types.SerializeInfo
        ) -> dict:
            if serializer is not None:
                for k, v in serialize_info.serialize().items():
                    data[f"{prefix}@{key}{k}"] = v
            return data

        data = common.pre_serialize(
            data, serializer=serializer, insert_serialize_info=_insert_serialize_info
        )

        with atomic.atomic_write_hdf5(path, h5group) as (h5file, h5group):
            dicttonx(
                treedict=data,
                h5file=h5file,
                h5path=h5group,
                update_mode=update_mode,
                add_nx_class=True,
            )
            self._set_nx_classes(h5file, self.path_in_file_parts())

    @staticmethod
    def _set_nx_classes(h5file, parts: List[str]):
        h5file.attrs["NX_class"] = "NXroot"
        h5group = h5file
        for i, name in enumerate(parts):
            h5group = h5group[name]
            if not isinstance(h5group, h5py.Group):
                break
            if i == 0:
                NX_class = "NXentry"
            elif i == 1:
                NX_class = "NXprocess"
            else:
                NX_class = "NXcollection"
            h5group.attrs["NX_class"] = NX_class

    def _load(self, path: Path, **kw) -> Any:
        h5group = self.path_in_file_parent
        h5name = self.path_in_file_name

        adict = nxtodict(h5file=str(path), path=h5group, **kw)

        def _pop_serialize_info(data: dict, key: str) -> Optional[types.SerializeInfo]:
            parent = data
            if h5name and isinstance(data[h5name], dict):
                parent = data[h5name]

            prefix = f"@{key}"
            nprefix = len(prefix)
            keys = [k for k in parent if k.startswith(prefix)]
            if not keys:
                return None

            serialize_info = {k[nprefix:]: parent.pop(k, None) for k in keys}
            return types.SerializeInfo.deserialize(serialize_info)

        adict = common.post_deserialize(adict, pop_serialize_info=_pop_serialize_info)

        if h5name:
            return adict[h5name]
        return adict
