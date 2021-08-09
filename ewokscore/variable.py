from typing import Union, Optional
from numbers import Integral
from collections.abc import Mapping, MutableMapping, Iterable, Sequence
import numpy

from .hashing import UniversalHashable
from .hashing import UniversalHash
from .persistence import instantiate_data_proxy
from .persistence.proxy import DataProxy
from .persistence.proxy import DataUri


def data_proxy_from_varinfo(
    hashable: UniversalHashable, varinfo
) -> Union[DataProxy, None]:
    root_uri = varinfo.get("root_uri")
    if not root_uri:
        return
    scheme = varinfo.get("scheme", "json")
    hashable = varinfo.get("__hashable", hashable)
    return instantiate_data_proxy(scheme, hashable, root_uri=root_uri)


class Variable(UniversalHashable):
    """Has a runtime value (python object) and a persistent value (disk or memory)."""

    def __init__(
        self,
        value=UniversalHashable.MISSING_DATA,
        uri: Optional[DataUri] = None,
        varinfo: Optional[dict] = None,
        **kw,
    ):
        """
        :param value: the runtime value
        :param dict varinfo:
        :param **kw: see `UniversalHashable`
        """
        if varinfo is None:
            varinfo = dict()
        elif not isinstance(varinfo, Mapping):
            raise TypeError(varinfo, type(varinfo))

        if uri:
            self._data_proxy = instantiate_data_proxy(uri.parse().scheme, uri)
            if self._data_proxy is None:
                raise ValueError("Invalid URI", uri)
        else:
            self._data_proxy = data_proxy_from_varinfo(self, varinfo)

        self._hashing_enabled = bool(varinfo.get("enable_hashing", False))
        self._hashing_enabled |= self._data_proxy is not None

        self._runtime_value = self.MISSING_DATA

        super().__init__(**kw)
        self.value = value

    @property
    def data_proxy(self):
        return self._data_proxy

    def _uhash_data(self):
        """The runtime value is used."""
        if self._hashing_enabled:
            return self._runtime_value
        else:
            return super()._uhash_data()

    def __eq__(self, other):
        if isinstance(other, UniversalHashable):
            return super().__eq__(other)
        else:
            return self.value == other

    @property
    def value(self):
        if self._runtime_value is self.MISSING_DATA:
            self.load(raise_error=False)
        return self._runtime_value

    @value.setter
    def value(self, v):
        self._runtime_value = v

    def dump(self) -> bool:
        """From runtime to persistent value (never overwrite).
        Creating the persistent value needs to be atomic.

        This silently returns when:
        - data persistence is disabled
        - already persisted
        - data does not have a runtime value (MISSING_DATA)
        - non value URI can be constructed
        """
        if (
            self.data_proxy is not None
            and not self.has_persistent_value
            and self.has_runtime_value
        ):
            return self.data_proxy.dump(self._serialize(self.value))
        return False

    def load(self, raise_error=True):
        """From persistent to runtime value. This is called when
        try to get the value (lazy loading).

        This silently returns when:
        - data persistence is disabled
        - uri is None (i.e. uhash is None)
        - raise_error=False
        """
        if self.data_proxy is not None:
            data = self.data_proxy.load(raise_error=raise_error)
            self._runtime_value = self._deserialize(data)

    def _serialize(self, value):
        """Before runtime to persistent"""
        return value

    def _deserialize(self, value):
        """Before persistent to runtime"""
        return value

    @property
    def has_persistent_value(self):
        return self._has_persistent_value()

    @property
    def has_runtime_value(self):
        return self._has_runtime_value()

    @property
    def has_value(self):
        return self.has_runtime_value or self.has_persistent_value

    def _has_persistent_value(self):
        return self.data_proxy is not None and self.data_proxy.exists()

    def _has_runtime_value(self):
        return self._runtime_value is not self.MISSING_DATA

    def force_non_existing(self):
        while self.has_persistent_value:
            self.uhash_randomize()


class VariableContainer(Mapping, Variable):
    """An immutable mapping of variable identifiers (str or int) to variables (Variable)."""

    def __init__(self, **kw):
        value = kw.pop("value", None)
        self.__varparams = dict(kw)
        self.__update_root_uri(kw, "output_info")
        self.__npositional_vars = 0
        self.__metadata = dict()
        self.__metadata_proxy = None
        super().__init__(**kw)
        if value:
            self._update(value)

    def __getitem__(self, key):
        return self.value[key]

    def _update(self, value):
        if isinstance(value, Mapping):
            value = value.items()
        if not isinstance(value, Iterable):
            raise TypeError(value, type(value))
        for i, tpl in enumerate(value):
            if not isinstance(tpl, Sequence):
                raise TypeError(
                    f"cannot convert dictionary update sequence element #{i} to a sequence"
                )
            if len(tpl) != 2:
                raise ValueError(
                    f"dictionary update sequence element #{i} has length {len(tpl)}; 2 is required"
                )
            self._set_item(*tpl)

    def _set_item(self, key, value):
        key = self._parse_variable_name(key)
        if isinstance(key, int):
            self._fill_missing_positions(key)
        if not self.container_has_value:
            self.value = dict()
        self.value[key] = self._create_variable(key, value)

    def _parse_variable_name(self, key):
        """Variables are identified by a `str` or an `int`. A key like "1" will
        be converted to an `int` (e.g. json dump converts `int` to  `str`).
        """
        if isinstance(key, str):
            if key.isdigit():
                key = int(key)
        if isinstance(key, Integral):
            key = int(key)
            if key < 0:
                raise ValueError("Negative argument positions are not allowed")
        elif not isinstance(key, str):
            raise TypeError(
                f"Variable {key} must be a string or positive integer", type(key)
            )
        return key

    def _fill_missing_positions(self, pos):
        nbefore = self.__npositional_vars
        nafter = max(nbefore, pos + 1)
        for i in range(nbefore, nafter - 1):
            self._set_item(i, self.MISSING_DATA)
        self.__npositional_vars = nafter

    @property
    def n_positional_variables(self):
        return self.__npositional_vars

    def _create_variable(self, key, value):
        if isinstance(value, Variable):
            return value
        varparams = dict(self.__varparams)
        if isinstance(value, UniversalHash):
            varparams["uhash"] = value
            varparams["instance_nonce"] = None
        elif isinstance(value, DataUri):
            varparams["uri"] = value
            varparams["uhash"] = value.uhash
            varparams["instance_nonce"] = None
        else:
            varparams["value"] = value
            instance_nonce = varparams.pop("instance_nonce", None)
            varparams["instance_nonce"] = instance_nonce, key
        self.__update_root_uri(varparams, "output_values/" + str(key))
        return Variable(**varparams)

    def __copy_varinfo(self, varparams) -> bool:
        varinfo = varparams.get("varinfo")
        if varinfo is None:
            varparams["varinfo"] = dict()
        else:
            varparams["varinfo"] = dict(varinfo)
        return varparams["varinfo"]

    def __update_root_uri(self, varparams, name) -> bool:
        """Update `root_uri` for formats that allows multiple
        variables in 1 file.
        """
        varinfo = varparams.get("varinfo")
        if not varinfo:
            return False
        root_uri = varinfo.get("root_uri", None)
        if not root_uri:
            return False
        if varinfo.get("scheme") != "nexus":
            return False  # format cannot store multiple variables
        if "name=" in root_uri:
            raise RuntimeError(f"name already specified in {repr(root_uri)}")
        varinfo = self.__copy_varinfo(varparams)
        if name:
            root_uri = f"{root_uri}?name={name}"
        varinfo["__hashable"] = self
        varinfo["root_uri"] = root_uri
        return True

    @property
    def metadata_proxy(self):
        varparams = dict(self.__varparams)
        if not self.__update_root_uri(varparams, None):
            return
        if self.__metadata_proxy is None:
            self.__metadata_proxy = data_proxy_from_varinfo(self, varparams["varinfo"])
        return self.__metadata_proxy

    @property
    def metadata(self) -> Union[dict, None]:
        if self.metadata_proxy is None:
            return None
        return self.__metadata

    def _dump_metadata(self):
        if self.metadata_proxy is None:
            return not bool(self.__metadata)
        return self.metadata_proxy.dump(self.__metadata, update_mode="modify")

    def __iter__(self):
        adict = self.value
        if isinstance(adict, dict):
            return iter(adict)
        else:
            return iter(tuple())

    def __len__(self):
        adict = self.value
        if isinstance(adict, dict):
            return len(adict)
        else:
            return 0

    def _serialize(self, value):
        return {k: v.data_proxy.uri.serialize() for k, v in self.items()}

    def _deserialize(self, value):
        if not value:
            return value
        adict = dict()
        for name, data in value.items():
            if name == "@NX_class":
                continue
            data = {
                k: v.item() if isinstance(v, numpy.ndarray) else v
                for k, v in data.items()
            }
            data = DataUri.deserialize(data)
            adict[name] = self._create_variable(name, data)
        return adict

    def dump(self):
        b = True
        for v in self.values():
            b &= v.dump()
        b &= super().dump()
        b &= self._dump_metadata()
        return b

    @property
    def container_has_persistent_value(self):
        return super()._has_persistent_value()

    def _has_persistent_value(self):
        if self.container_has_persistent_value:
            return all(v.has_persistent_value for v in self.values())
        else:
            return False

    @property
    def container_has_runtime_value(self):
        return super()._has_runtime_value()

    def _has_runtime_value(self):
        if self.container_has_runtime_value:
            return all(v.has_runtime_value for v in self.values())
        else:
            return False

    @property
    def container_has_value(self):
        return self.container_has_runtime_value or self.container_has_persistent_value

    def force_non_existing(self):
        super().force_non_existing()
        for v in self.values():
            v.force_non_existing()

    @property
    def variable_uhashes(self):
        return self._serialize(self.value)

    @property
    def variable_values(self):
        return {k: v.value for k, v in self.items()}

    @property
    def variable_data_proxies(self):
        return {k: v.data_proxy for k, v in self.items()}

    @property
    def variable_uris(self):
        return {k: v.data_proxy.uri for k, v in self.items()}

    @property
    def variable_transfer_data(self):
        """Transfer data by variable or URI"""
        return {
            k: v.data_proxy.uri if v.has_persistent_value else v
            for k, v in self.items()
        }

    @property
    def named_variable_values(self):
        return {k: v.value for k, v in self.items() if isinstance(k, str)}

    @property
    def positional_variable_values(self):
        values = [self.MISSING_DATA] * self.__npositional_vars
        for i, var in self.items():
            if isinstance(i, int):
                values[i] = var.value
        return tuple(values)


def variable_from_transfer(data, varinfo=None) -> Variable:
    """Meant for task schedulers that pass data (see `VariableContainer.variable_transfer_data`)"""
    if isinstance(data, Variable):
        return data
    kw = {"varinfo": varinfo}
    if isinstance(data, UniversalHash):
        kw["uhash"] = data
    elif isinstance(data, DataUri):
        kw["uri"] = data
    else:
        kw["value"] = data
    return Variable(**kw)


def value_from_transfer(data, varinfo=None):
    """Meant for task schedulers that pass data (see VariableContainer.variable_transfer_*)"""
    if isinstance(data, Variable):
        return data.value
    if isinstance(data, UniversalHash):
        kw = {"varinfo": varinfo}
        kw["uhash"] = data
    elif isinstance(data, DataUri):
        kw = {"varinfo": varinfo}
        kw["uri"] = data
    else:
        return data
    return Variable(**kw).value


class MutableVariableContainer(VariableContainer, MutableMapping):
    """An mutable mapping of variable identifiers (str or int) to variables (Variable)."""

    def __setitem__(self, key, value):
        self._set_item(key, value)

    def __delitem__(self, key):
        adict = self.value
        if isinstance(adict, dict):
            del self.value[key]

    def update_values(self, items):
        if isinstance(items, Mapping):
            items = items.items()
        for k, v in items:
            self[k].value = v


class MissingVariableError(RuntimeError):
    pass


class ReadOnlyVariableError(RuntimeError):
    pass


class ReadOnlyVariableContainerNamespace:
    """Expose getting variable values through attributes and indexing"""

    def __init__(self, container):
        self._container = container

    _RESERVED_VARIABLE_NAMES = None

    @classmethod
    def _reserved_variable_names(cls):
        if cls._RESERVED_VARIABLE_NAMES is None:
            cls._RESERVED_VARIABLE_NAMES = set(dir(cls)) | {"_container"}
        return cls._RESERVED_VARIABLE_NAMES

    def __setattr__(self, attrname, value):
        if attrname == "_container":
            super().__setattr__(attrname, value)
        else:
            self._get_variable(attrname)
            raise ReadOnlyVariableError(attrname)

    def __getattr__(self, attrname):
        return self[attrname]

    def __getitem__(self, key):
        return self._get_variable(key).value

    def _get_variable(self, key):
        try:
            return self._container[key]
        except (KeyError, TypeError):
            raise MissingVariableError(key)


class VariableContainerNamespace(ReadOnlyVariableContainerNamespace):
    """Expose getting and setting variable values through attributes and indexing"""

    def __setattr__(self, attrname, value):
        if attrname == "_container":
            super().__setattr__(attrname, value)
        else:
            self._get_variable(attrname).value = value
