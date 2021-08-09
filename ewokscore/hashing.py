import random
import hashlib
from typing import Union
from collections.abc import Mapping, Iterable, Set
import numpy
from .utils import qualname


def classhashdata(cls):
    """
    :returns bytes:
    """
    return qualname(cls).encode()


def multitype_sorted(sequence, key=None):
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


def uhash(value, _hash=None):
    """Universial hash (as opposed to python's hash).
    This is an example. Must find something better.

    :param value:
    :param _hash: for internal recursive calls
    :returns UniversalHash:
    """
    # Avoid using python's hash!
    bdigest = _hash is None
    if bdigest:
        _hash = hashlib.sha256()
    _hash.update(classhashdata(type(value)))
    if value is None:
        pass
    elif isinstance(value, UniversalHashable):
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
        keys, values = zip(*multitype_sorted(value.items(), key=lambda item: item[0]))
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
        raise TypeError(value, type(value))
    if bdigest:
        return UniversalHash(_hash.hexdigest())


class UniversalHash:
    def __init__(self, hexdigest):
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


class MissingData:
    def __bool__(self):
        return False

    def __repr__(self):
        return "<MISSING_DATA>"


class UniversalHashable:
    """The universal hash of an instance is:
        * data
        * class nonce (class qualname, class version, superclass nonce)
        * instance nonce (if any)

    When a uhash is provided to the constructor however:
        * the provided uhash
        * instance nonce (if any)
    """

    __CLASS_NONCE = None
    __VERSION = None
    MISSING_DATA = MissingData()

    def __init__(self, uhash=None, instance_nonce=None):
        """
        :param str, bytes, UniversalHash, UniversalHashable uhash:
        :param instance_nonce:
        """
        self.__set_uhash(uhash)
        self.__original_uhash = self.__uhash
        self.__instance_nonce = instance_nonce
        self.__original__instance_nonce = instance_nonce

    def __init_subclass__(subcls, version=None, **kwargs):
        super().__init_subclass__(**kwargs)
        supercls_data = subcls.class_nonce()
        subcls.__VERSION = version
        subcls_data = subcls.class_nonce_data()
        subcls.__CLASS_NONCE = str(uhash((subcls_data, supercls_data)))

    @classmethod
    def class_nonce(cls):
        return cls.__CLASS_NONCE

    @classmethod
    def class_nonce_data(cls):
        return qualname(cls), cls.__VERSION

    def instance_nonce(self):
        return self.__instance_nonce

    def __set_uhash(self, uhash):
        if uhash is None:
            self.__uhash = None
        elif isinstance(uhash, (str, bytes)):
            self.__uhash = UniversalHash(uhash)
        elif isinstance(uhash, (UniversalHash, UniversalHashable)):
            self.__uhash = uhash
        else:
            raise TypeError(uhash, type(uhash))

    def fix_uhash(self):
        if self.__uhash is not None:
            return
        keep, self.__instance_nonce = self.__instance_nonce, None
        try:
            uhash = self.uhash
        finally:
            self.__instance_nonce = keep
        self.__set_uhash(uhash)

    def undo_fix_uhash(self):
        self.__uhash = self.__original_uhash

    @property
    def uhash(self) -> Union[None, UniversalHash]:
        _uhash = self.__uhash
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
            if isinstance(_uhash, UniversalHashable):
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

    def __hash__(self):
        # make it python hashable (to use in sets and dict keys)
        uhash = self.uhash
        if uhash is None:
            return hash(id(self))
        else:
            return hash(uhash)

    def __eq__(self, other):
        if isinstance(other, UniversalHashable):
            uhash = other.uhash
        elif isinstance(other, UniversalHash):
            uhash = other
        else:
            raise TypeError(other, type(other))
        return self.uhash == uhash

    def __repr__(self):
        uhash = self.uhash
        if uhash is None:
            return super().__repr__()
        else:
            return f"{super().__repr__()}(uhash='{uhash}')"

    def __str__(self):
        uhash = self.uhash
        if uhash is None:
            return qualname(type(self))
        else:
            return f"{qualname(type(self))}(uhash='{uhash}')"
