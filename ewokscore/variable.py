from typing import Any, Dict, Optional
from numbers import Integral
from collections.abc import Mapping, MutableMapping, Iterable, Sequence

from . import hashing
from .persistence import instantiate_data_proxy
from .persistence.proxy import DataProxy
from .persistence.proxy import DataUri


def data_proxy_from_varinfo(
    uhash_source: hashing.UniversalHashable, varinfo
) -> Optional[DataProxy]:
    root_uri = varinfo.get("root_uri")
    if not root_uri and not varinfo.get("has_data_proxy"):
        return
    relative_uri = varinfo.get("relative_uri")
    scheme = varinfo.get("scheme", "json")
    return instantiate_data_proxy(
        scheme=scheme,
        root_uri=root_uri,
        relative_uri=relative_uri,
        uhash_source=uhash_source,
    )


CONTAINER_URI_NAME = "task_results"


class Variable(hashing.UniversalHashable):
    """Has a runtime value (python object) and a persistent value (disk or memory).
    The location of the persistent value is either provided or derived from the
    universal hash of the variable, which itself can be provided or derived from the
    variable data.
    """

    def __init__(
        self,
        value=hashing.UniversalHashable.MISSING_DATA,
        metadata=hashing.UniversalHashable.MISSING_DATA,
        varinfo: Optional[dict] = None,
        data_uri: Optional[DataUri] = None,
        data_proxy: Optional[DataProxy] = None,
        pre_uhash: Optional[hashing.PreUhashTypes] = None,
        instance_nonce: Optional[Any] = None,
    ):
        if varinfo is None:
            varinfo = dict()
        elif not isinstance(varinfo, Mapping):
            raise TypeError(varinfo, type(varinfo))

        if data_proxy is not None:
            pre_uhash = data_proxy.uri.uhash
            instance_nonce = None
            self._data_proxy = data_proxy
        elif data_uri is not None:
            pre_uhash = data_uri.uhash
            instance_nonce = None
            self._data_proxy = instantiate_data_proxy(uri=data_uri)
            if self._data_proxy is None:
                raise ValueError("Invalid URI", data_uri)
        else:
            self._data_proxy = data_proxy_from_varinfo(
                uhash_source=self, varinfo=varinfo
            )

        self._hashing_enabled = bool(varinfo.get("enable_hashing", False))
        self._hashing_enabled |= self._data_proxy is not None

        self._runtime_value = self.MISSING_DATA
        if metadata == self.MISSING_DATA:
            metadata = dict()
        self._runtime_metadata = metadata

        super().__init__(pre_uhash=pre_uhash, instance_nonce=instance_nonce)
        self.value = value

    def copy_without_references(self):
        """Copy that does not contain references to uhashable objects"""
        kwargs = self.get_uhash_init(serialize=True)
        kwargs["data_proxy"] = self.data_proxy
        return type(self)(value=self.value, **kwargs)

    @property
    def data_proxy(self) -> Optional[DataProxy]:
        return self._data_proxy

    @property
    def data_uri(self) -> Optional[DataUri]:
        if self._data_proxy is None:
            return None
        return self.data_proxy.uri

    @property
    def hashing_enabled(self):
        return self._hashing_enabled

    def _uhash_data(self):
        """The runtime value is used."""
        if self._hashing_enabled:
            return self._runtime_value
        else:
            return super()._uhash_data()

    def __eq__(self, other):
        if isinstance(other, hashing.HasUhash):
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

    @property
    def metadata(self) -> dict:
        return self._runtime_metadata

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
            return self.data_proxy.dump(self.serialize())
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
            if data is not self.MISSING_DATA:
                self.deserialize(data)

    def serialize(self) -> dict:
        """Serialize data before persistent storage"""
        data = dict(self.metadata)
        data["value"] = self.value
        return data

    def deserialize(self, data: dict):
        """Deserialize data after loading from persistent storage"""
        self._runtime_value = data.pop("value")
        self._runtime_metadata = data

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


class VariableContainer(Variable, Mapping):
    """An immutable mapping of variable identifiers (str or int) to variables (Variable)."""

    def __init__(
        self,
        value=hashing.UniversalHashable.MISSING_DATA,
        varinfo: Optional[dict] = None,
        data_uri: Optional[DataUri] = None,
        data_proxy: Optional[DataProxy] = None,
        pre_uhash: Optional[hashing.PreUhashTypes] = None,
        instance_nonce: Optional[Any] = None,
    ):
        varparams = {
            "pre_uhash": pre_uhash,
            "instance_nonce": instance_nonce,
            "varinfo": varinfo,
        }
        self.__add_relative_uri(varparams, path=CONTAINER_URI_NAME)

        self.__varparams = varparams
        self.__npositional_vars = 0
        super().__init__(data_uri=data_uri, data_proxy=data_proxy, **varparams)
        if value:
            self._update(value)

    def fix_uhash(self):
        for var in self.values():
            var.fix_uhash()
        return super().fix_uhash()

    def cleanup_references(self):
        """Remove all references to other hashables.
        Side effect: fixes the uhash when it depends on another hashable.
        """
        for var in self.values():
            var.cleanup_references()
        pre_uhash = self.__varparams.get("pre_uhash")
        if isinstance(pre_uhash, hashing.HasUhash):
            self.__varparams["pre_uhash"] = pre_uhash.uhash
        return super().cleanup_references()

    def copy_without_references(self):
        """The uhash of the copy is fixed thereby remove references to other uhashable objects."""
        return type(self)(
            value={name: var.copy_without_references() for name, var in self.items()},
            **self.__varparams,
        )

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

    def _create_variable(self, name, value):
        if isinstance(value, Variable):
            return value
        varparams = dict()
        if isinstance(value, DataUri):
            varparams["data_uri"] = value
        elif isinstance(value, DataProxy):
            varparams["data_proxy"] = value
        elif isinstance(value, (hashing.UniversalHash, hashing.HasUhash)):
            varparams.update(self.__varparams)
            varparams["pre_uhash"] = value
            varparams["instance_nonce"] = None
        else:
            varparams.update(self.__varparams)
            varparams["value"] = value
            instance_nonce = varparams.pop("instance_nonce", None)
            varparams["instance_nonce"] = instance_nonce, name
            self.__add_relative_uri(varparams, path=f"{name}")
        return Variable(**varparams)

    def __copy_varinfo(self, varparams) -> Dict:
        varinfo = varparams.get("varinfo")
        if varinfo is None:
            varparams["varinfo"] = dict()
        else:
            varparams["varinfo"] = dict(varinfo)
        return varparams["varinfo"]

    def __add_relative_uri(self, varparams, path: Optional[str] = None) -> bool:
        """Modify the general `root_uri` for a specific case."""
        varinfo = varparams.get("varinfo")
        if not varinfo or not varinfo.get("root_uri"):
            return False
        varinfo = self.__copy_varinfo(varparams)
        if path:
            if varinfo.get("relative_uri"):
                varinfo["relative_uri"] += f"&path={path}"
            else:
                varinfo["relative_uri"] = f"?path={path}"
        return True

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

    def serialize(self):
        """Serialize data before persistent storage"""
        data = dict(self.metadata)
        data[CONTAINER_URI_NAME] = {
            name: var.data_proxy.serialize()
            for name, var in self.value.items()
            if var.data_proxy is not None
        }
        return data

    def deserialize(self, data: dict):
        """Deserialize data after loading from persistent storage"""
        variables = data.pop(CONTAINER_URI_NAME)
        value = dict()
        for name, data_proxy in variables.items():
            data_proxy = DataProxy.deserialize(data_proxy)
            if data_proxy is None:
                continue
            value[name] = self._create_variable(name, data_proxy)
        self._runtime_value = value
        self._runtime_metadata = data

    def dump(self):
        b = True
        for v in self.values():
            b &= v.dump()
        b &= super().dump()
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
        return {name: var.uhash for name, var in self.items()}

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
        data = dict()
        for name, var in self.items():
            if var.has_persistent_value:
                data[name] = var.data_proxy.uri
            elif var.hashing_enabled:
                # Remove possible references to a uhashable
                data[name] = var.copy_without_references()
            else:
                data[name] = var.value
        return data

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
    if isinstance(data, DataProxy):
        kw["data_proxy"] = data
    elif isinstance(data, DataUri):
        kw["data_uri"] = data
    elif isinstance(data, (hashing.UniversalHash, hashing.HasUhash)):
        kw["pre_uhash"] = data
    else:
        kw["value"] = data
    return Variable(**kw)


def value_from_transfer(data, varinfo=None):
    """Meant for task schedulers that pass data (see VariableContainer.variable_transfer_*)"""
    if isinstance(data, Variable):
        return data.value
    kw = {"varinfo": varinfo}
    if isinstance(data, DataProxy):
        kw["data_proxy"] = data
    elif isinstance(data, DataUri):
        kw["data_uri"] = data
    elif isinstance(data, (hashing.UniversalHash, hashing.HasUhash)):
        kw["pre_uhash"] = data
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
