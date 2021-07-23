import os
import string
import random
import json
from numbers import Integral
from collections.abc import Mapping, MutableMapping, Iterable, Sequence
from contextlib import contextmanager
from . import hashing


class PersistencyError(RuntimeError):
    pass


class UriNotFoundError(PersistencyError):
    pass


def random_string(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def nonexisting_tmp_file(filename):
    tmpname = filename + ".tmp" + random_string(6)
    while os.path.exists(tmpname):
        tmpname = filename + ".tmp" + random_string(6)
    return tmpname


@contextmanager
def atomic_write(filename):
    tmpname = nonexisting_tmp_file(filename)
    dirname = os.path.dirname(tmpname)
    try:
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(tmpname, mode="w") as f:
            yield f
    except Exception:
        try:
            os.unlink(tmpname)
        except FileNotFoundError:
            pass
        raise
    os.rename(tmpname, filename)


class Variable(hashing.UniversalHashable):
    """Has a runtime value (python object) and a persistent value (JSON).

    TODO: make abstraction of persistent medium
    """

    def __init__(
        self, value=hashing.UniversalHashable.MISSING_DATA, varinfo=None, **kw
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
        self._root_uri = varinfo.get("root_uri")
        self._disable_persistency = not self._root_uri
        self._runtime_value = self.MISSING_DATA
        super().__init__(**kw)
        self.value = value

    def _uhash_data(self):
        """The runtime value is used."""
        if self._disable_persistency:
            return super()._uhash_data()
        else:
            return self._runtime_value

    def __eq__(self, other):
        if isinstance(other, hashing.UniversalHashable):
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
    def uri(self):
        """uri of the persistent value

        :returns str or None: returns None when uhash is None
        """
        uhash = self.uhash
        if uhash is None:
            return
        filename = str(uhash) + ".json"
        if self._root_uri:
            filename = os.path.join(self._root_uri, filename)
        return filename

    def dump(self):
        """From runtime to persistent value (never overwrite).
        Creating the persistent value needs to be atomic.

        This silently returns when:
        - persistency is disabled
        - already persisted
        - data does not have a runtime value (MISSING_DATA)
        - non value URI can be constructed
        """
        if (
            self._disable_persistency
            or self.has_persistent_value
            or not self.has_runtime_value
        ):
            return
        filename = self.uri
        if not filename:
            return
        data = self.value
        with atomic_write(filename) as f:
            json.dump(self._serialize(data), f)

    def load(self, raise_error=True):
        """From persistent to runtime value. This is called when
        try to get the value (lazy loading).

        This silently returns when:
        - persistency is disabled
        - uri is None (i.e. uhash is None)
        - raise_error=False
        """
        if self._disable_persistency:
            return
        filename = self.uri
        if not filename:
            return
        try:
            with open(filename, mode="r") as f:
                self._runtime_value = self._deserialize(json.load(f))
        except FileNotFoundError as e:
            if raise_error:
                raise UriNotFoundError(filename) from e
        except Exception as e:
            if raise_error:
                raise PersistencyError(filename) from e

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
        try:
            return self._has_runtime_value()
        except PersistencyError:
            # Lazy loading failed
            return False

    @property
    def has_value(self):
        return self.has_runtime_value or self.has_persistent_value

    def _has_persistent_value(self):
        filename = self.uri
        if filename:
            return os.path.isfile(filename)
        else:
            return False

    def _has_runtime_value(self):
        return self._runtime_value is not self.MISSING_DATA

    def force_non_existing(self):
        while self.has_persistent_value:
            self.uhash_randomize()


class VariableContainer(Mapping, Variable):
    """An immutable mapping of variable identifiers (str or int) to variables (Variable)."""

    def __init__(self, **kw):
        value = kw.pop("value", None)
        self.__varparams = kw
        self.__npositional_vars = 0
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
        if isinstance(value, hashing.UniversalHash):
            varparams["uhash"] = value
            varparams["instance_nonce"] = None
        else:
            varparams["value"] = value
            instance_nonce = varparams.pop("instance_nonce", None)
            varparams["instance_nonce"] = instance_nonce, key
        return Variable(**varparams)

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
        return {k: str(v.uhash) for k, v in self.items()}

    def _deserialize(self, value):
        adict = dict()
        varparams = dict(self.__varparams)
        varparams["instance_nonce"] = None
        for k, v in value.items():
            varparams["uhash"] = hashing.UniversalHash(v)
            adict[k] = Variable(**varparams)
        return adict

    def dump(self):
        for v in self.values():
            v.dump()
        super().dump()

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
    def variable_transfer_data(self):
        return {k: v.uhash if v.has_persistent_value else v for k, v in self.items()}

    @property
    def variable_transfer_values(self):
        return {
            k: v.uhash if v.has_persistent_value else v.value for k, v in self.items()
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

    def update_values(self, items):
        if isinstance(items, Mapping):
            items = items.items()
        for k, v in items:
            self[k].value = v


class MutableVariableContainer(VariableContainer, MutableMapping):
    """An mutable mapping of variable identifiers (str or int) to variables (Variable)."""

    def __setitem__(self, key, value):
        self._set_item(key, value)

    def __delitem__(self, key):
        adict = self.value
        if isinstance(adict, dict):
            del self.value[key]


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
