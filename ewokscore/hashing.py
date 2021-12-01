import random
import hashlib
from typing import Any, Optional, Type, Union
from collections.abc import Mapping, Iterable, Set
import numpy
from .utils import qualname


def classhashdata(cls: Type) -> bytes:
    return qualname(cls).encode()


def multitype_sorted(sequence: Iterable, key=None) -> list:
    try:
        return sorted(sequence, key=key)
    except TypeError:
        pass
    if key is None:

        def key(item):
            return item

    adict = dict()
    for item in sequence:
        typename = type(key(item)).__name__
        adict.setdefault(typename, list()).append(item)

    return [
        item
        for _, items in sorted(adict.items(), key=lambda tpl: tpl[0])
        for item in sorted(items, key=key)
    ]


class UniversalHash:
    def __init__(self, hexdigest: Union[str, bytes]):
        if isinstance(hexdigest, bytes):
            hexdigest = hexdigest.decode()
        if not isinstance(hexdigest, str):
            raise TypeError(hexdigest, type(hexdigest))
        self._hexdigest = hexdigest

    def __hash__(self):
        # make it python hashable (to use in sets and dict keys)
        return hash(self._hexdigest)

    def __repr__(self):
        return "UniversalHash('{}')".format(self)

    def __str__(self):
        return self._hexdigest

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return str(self) < str(other)


def uhash(value, _hash=None) -> UniversalHash:
    """Universial hash (as opposed to python's `hash`)."""
    # Avoid using python's hash!
    bdigest = _hash is None
    if bdigest:
        _hash = hashlib.sha256()
    _hash.update(classhashdata(type(value)))
    if value is None:
        pass
    elif isinstance(value, HasUhash):
        _hash.update(repr(value.uhash).encode())
    elif isinstance(value, UniversalHash):
        _hash.update(repr(value).encode())
    elif isinstance(value, bytes):
        _hash.update(value)
    elif isinstance(value, str):
        _hash.update(value.encode())
    elif isinstance(value, int):
        _hash.update(hex(value).encode())
    elif isinstance(value, float):
        _hash.update(value.hex().encode())
    elif isinstance(value, (numpy.ndarray, numpy.number)):
        _hash.update(value.tobytes())
    elif isinstance(value, Mapping):
        lst = multitype_sorted(value.items(), key=lambda item: item[0])
        if lst:
            keys, values = zip(*lst)
        else:
            keys = values = list()
        uhash(keys, _hash=_hash)
        uhash(values, _hash=_hash)
    elif isinstance(value, Set):
        values = multitype_sorted(value)
        uhash(values, _hash=_hash)
    elif isinstance(value, Iterable):
        # Ordered
        for v in value:
            uhash(v, _hash=_hash)
    else:
        # TODO: register custom types
        raise TypeError(f"cannot uhash {value} (type: {type(value)})")
    if bdigest:
        return UniversalHash(_hash.hexdigest())


class HasUhash:
    @property
    def uhash(self) -> Optional[UniversalHash]:
        raise NotImplementedError

    def __hash__(self):
        # make it python hashable (to use in sets and dict keys)
        uhash = self.uhash
        if uhash is None:
            return hash(id(self))
        else:
            return hash(uhash)

    def __eq__(self, other):
        if isinstance(other, HasUhash):
            uhash = other.uhash
        elif isinstance(other, UniversalHash):
            uhash = other
        else:
            raise TypeError(other, type(other))
        return self.uhash == uhash

    def _get_repr_data(self) -> dict:
        data = dict()
        uhash = self.uhash
        if uhash is None:
            data["uhash"] = None
        else:
            data["uhash"] = repr(str(uhash))
        return data

    def __repr__(self):
        data = self._get_repr_data()
        if data:
            sdata = ", ".join([f"{k}={v}" for k, v in data.items()])
            return f"{super().__repr__()}({sdata})"
        else:
            return super().__repr__()

    def __str__(self):
        data = self._get_repr_data()
        if data:
            sdata = ", ".join([f"{k}={v}" for k, v in data.items()])
            return f"{qualname(type(self))}({sdata})"
        else:
            return qualname(type(self))


class MissingData:
    def __bool__(self):
        return False

    def __repr__(self):
        return "<MISSING_DATA>"

    def __eq__(self, other) -> bool:
        return isinstance(other, type(self))


PreUhashTypes = Union[str, bytes, UniversalHash, HasUhash]


class UniversalHashable(HasUhash):
    """The universal hash of an instance of this class is based on:
        * pre-uhash
        * instance nonce (if any)
    The universal hash is equal to the pre-hash when an instance nonce is not provided.

    The pre-uhash is either provided or based on:
        * data
        * class nonce (class qualifier name, class version, superclass nonce)
    """

    __CLASS_NONCE = None
    __VERSION = None
    MISSING_DATA = MissingData()

    def __init__(
        self,
        pre_uhash: Optional[PreUhashTypes] = None,
        instance_nonce: Optional[Any] = None,
    ):
        self.set_uhash_init(pre_uhash=pre_uhash, instance_nonce=instance_nonce)

    def __init_subclass__(subcls, version=None, **kwargs):
        super().__init_subclass__(**kwargs)
        supercls_data = subcls.class_nonce()
        subcls.__VERSION = version
        subcls_data = subcls.class_nonce_data()
        subcls.__CLASS_NONCE = str(uhash((subcls_data, supercls_data)))

    def set_uhash_init(
        self,
        pre_uhash: Optional[PreUhashTypes] = None,
        instance_nonce: Optional[Any] = None,
    ):
        self.__set_pre_uhash(pre_uhash)
        self.__original_pre_uhash = self.__pre_uhash
        self.__instance_nonce = instance_nonce
        self.__original__instance_nonce = instance_nonce

    def get_uhash_init(self, serialize=False):
        pre_uhash = self.__original_pre_uhash
        if serialize:
            if isinstance(pre_uhash, HasUhash):
                pre_uhash = str(pre_uhash.uhash)
            elif isinstance(pre_uhash, UniversalHash):
                pre_uhash = str(pre_uhash)
        return {
            "pre_uhash": pre_uhash,
            "instance_nonce": self.__original__instance_nonce,
        }

    def __set_pre_uhash(self, pre_uhash):
        if pre_uhash is None:
            self.__pre_uhash = None
        elif isinstance(pre_uhash, (str, bytes)):
            self.__pre_uhash = UniversalHash(pre_uhash)
        elif isinstance(pre_uhash, (UniversalHash, HasUhash)):
            self.__pre_uhash = pre_uhash
        else:
            raise TypeError(pre_uhash, type(pre_uhash))

    @classmethod
    def class_nonce(cls):
        return cls.__CLASS_NONCE

    @classmethod
    def class_nonce_data(cls):
        return qualname(cls), cls.__VERSION

    def instance_nonce(self):
        return self.__instance_nonce

    def fix_uhash(self):
        """Fix the uhash when it is derived from the uhash data."""
        if self.__pre_uhash is not None:
            return
        keep, self.__instance_nonce = self.__instance_nonce, None
        try:
            pre_uhash = self.uhash
        finally:
            self.__instance_nonce = keep
        self.__set_pre_uhash(pre_uhash)

    def undo_fix_uhash(self):
        self.__pre_uhash = self.__original_pre_uhash

    def cleanup_references(self):
        """Remove all references to other hashables.
        Side effect: fixes the uhash when it depends on another hashable.
        """
        if isinstance(self.__pre_uhash, HasUhash):
            pre_uhash = self.__pre_uhash.uhash
            self.__pre_uhash = pre_uhash
            self.__original_pre_uhash = pre_uhash

    @property
    def uhash(self) -> Optional[UniversalHash]:
        _uhash = self.__pre_uhash
        if _uhash is None:
            data = self._uhash_data()
            if data is self.MISSING_DATA:
                return None
            cnonce = self.class_nonce()
            inonce = self.instance_nonce()
            if inonce is None:
                return uhash((data, cnonce))
            else:
                return uhash((data, cnonce, inonce))
        else:
            if isinstance(_uhash, HasUhash):
                _uhash = _uhash.uhash
                if _uhash is None:
                    return None
            inonce = self.instance_nonce()
            if inonce is None:
                return _uhash
            else:
                return uhash((_uhash, inonce))

    def _uhash_data(self):
        return self.MISSING_DATA

    def uhash_randomize(self):
        self.__instance_nonce = random.randint(-1e100, 1e100)

    def undo_randomize(self):
        self.__instance_nonce = self.__original__instance_nonce
