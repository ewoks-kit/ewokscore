"""Universal hashing independent of the current process"""

import datetime
import enum
import hashlib
import pathlib
import secrets
import uuid
from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Mapping
from collections.abc import Set
from functools import singledispatch
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import Union

import numpy
from ewoksutils.import_utils import qualname

from . import missing_data
from .entry_points import entry_points


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


def uhash(value) -> UniversalHash:
    """Universal hash (as opposed to python's `hash`).

    A type is universally hashable when it implements `__uhash__`, which returns
    either a `UniversalHash` or another universally hashable value.
    """
    if not _LOADED_UHASH_REGISTRATIONS:
        load_uhash_registrations()
    return _uhash(value)


def _unregistered_uhash(value: Any) -> Any:
    """Placeholder for types without a registered universal hash."""
    raise TypeError(f"universal unhashable type: {type(value)}")


# Dispatches base on the type of the first argument, the value.
_REGISTERED_UHASH = singledispatch(_unregistered_uhash)


# Avoids the dispatch when nothing is registered
_HAS_REGISTERED_UHASH = False


def register_uhash(cls: Type, method: Callable[[Any], Any]) -> None:
    """Make instances of `cls` universally hashable, for types that cannot
    implement `__uhash__` themselves. `method` returns either a `UniversalHash`
    or another universally hashable value.
    """
    global _HAS_REGISTERED_UHASH
    _REGISTERED_UHASH.register(cls, method)
    _HAS_REGISTERED_UHASH = True


_LOADED_UHASH_REGISTRATIONS = False


def load_uhash_registrations() -> None:
    """Apply the registrations of the `ewoks.hashing` entry point group."""
    global _LOADED_UHASH_REGISTRATIONS
    # Set before loading: a registration is allowed to hash values itself
    _LOADED_UHASH_REGISTRATIONS = True
    for entrypoint in entry_points("ewoks.hashing"):
        entrypoint.load()()


# `_uhash` serializes a value to a byte stream and hashes that stream with
# SHA-256. The stream is a depth-first walk over the value in which
#
#  * a scalar contributes its type name followed by its data
#  * a container contributes its type name, then its items, then `)`
#  * a container that occurs inside itself contributes `^` followed by the
#    number of levels up to that container
#
# The stream has to be unambiguous, or values collide. The closing `)` is what
# separates `[1, [2]]` from `[[1, 2]]`, and data of an arbitrary length is
# prefixed with that length so it cannot pose as the data around it.
def _uhash(value) -> UniversalHash:
    if isinstance(value, UniversalHash):
        return value

    _hash = hashlib.sha256()
    # What is left to serialize, in reverse order because the stack is LIFO
    stack: List[Any] = [value]
    # The values being expanded, from the root down to the current one
    open_depths: Dict[int, int] = dict()  # id -> depth
    at_root = True

    while stack:
        value = stack.pop()

        if type(value) is _EndOfNesting:
            # All items of `value.nested` are serialized, so close it
            _hash.update(_END_OF_NESTING)
            del open_depths[id(value.nested)]
            continue

        depth = open_depths.get(id(value))
        if depth is not None:
            # `value` occurs inside itself: serialize the number of levels up to
            # the enclosing occurrence instead of expanding it a second time
            _hash.update(_BACK_REFERENCE)
            _hash.update(str(len(open_depths) - depth).encode())
            continue

        # Universal hash method to apply to value: __uhash__
        uhash_method = getattr(type(value), "__uhash__", None)

        # Universal hash method to apply to value: registered for the value type
        if uhash_method is None and _HAS_REGISTERED_UHASH:
            uhash_method = _REGISTERED_UHASH.dispatch(type(value))
            if uhash_method is _unregistered_uhash:
                uhash_method = None

        # Apply universal hash method to the value
        if uhash_method is not None:
            nested = uhash_method(value)

            # The root value provides its universal hash directly
            if at_root and isinstance(nested, UniversalHash):
                return nested

            # Any other return value is the content of the value
            at_root = False
            _hash.update(_classhashdata(type(value)))
            _expand(stack, open_depths, value, (nested,))
            continue

        # No universal hash method: serialize the value by its type
        at_root = False

        _hash.update(_classhashdata(type(value)))

        if value is None:
            pass
        elif isinstance(value, UniversalHash):
            _hash.update(repr(value).encode())
        elif isinstance(value, enum.Enum):
            # The name identifies the member, except for a combination of flags
            _expand(stack, open_depths, value, (value.name, value.value))
        elif isinstance(value, (bytes, bytearray)):
            _update_data(_hash, bytes(value))
        elif isinstance(value, str):
            _update_data(_hash, value.encode())
        elif isinstance(value, int):
            _hash.update(hex(value).encode())
        elif isinstance(value, float):
            _hash.update(value.hex().encode())
        elif isinstance(value, complex):
            _hash.update(value.real.hex().encode())
            _hash.update(value.imag.hex().encode())
        elif isinstance(value, datetime.datetime):
            # Equal datetimes have equal universal hashes: aware datetimes are
            # equal when they refer to the same instant, naive datetimes when
            # they have the same wall clock time
            offset = value.utcoffset()
            if offset is None:
                _hash.update(b"naive")
                _update_data(_hash, value.isoformat().encode())
            else:
                _hash.update(b"aware")
                utc = value.replace(tzinfo=None) - offset
                _update_data(_hash, utc.isoformat().encode())
        elif isinstance(value, datetime.date):
            _update_data(_hash, value.isoformat().encode())
        elif isinstance(value, datetime.time):
            _update_data(_hash, value.isoformat().encode())
        elif isinstance(value, datetime.timedelta):
            # Normalized by the constructor
            _update_data(
                _hash, f"{value.days}:{value.seconds}:{value.microseconds}".encode()
            )
        elif isinstance(value, uuid.UUID):
            _hash.update(value.bytes)
        elif isinstance(value, pathlib.PurePath):
            _update_data(_hash, str(value).encode())
        elif isinstance(value, (numpy.ndarray, numpy.generic)):
            # `tobytes` contains neither the data type nor the shape, which
            # together determine the length of the data
            _update_data(_hash, str(value.dtype).encode())
            _update_data(_hash, str(value.shape).encode())
            if value.dtype.hasobject:
                # `tobytes` contains pointers, which differ between processes
                _expand(stack, open_depths, value, value.flat)
            elif isinstance(value, numpy.ndarray) and value.flags.c_contiguous:
                _hash.update(value)  # `tobytes` would copy the array
            else:
                _hash.update(value.tobytes())
        elif isinstance(value, Mapping):
            items = _multitype_sorted(value.items(), key=lambda item: item[0])
            if items:
                keys, values = zip(*items)
            else:
                keys = values = tuple()
            _expand(stack, open_depths, value, (keys, values))
        elif isinstance(value, Set):
            _expand(stack, open_depths, value, _multitype_sorted(value))
        elif isinstance(value, Iterator):
            # Hashing consumes an iterator, so its hash is not reproducible
            raise TypeError(f"universal unhashable iterator: {type(value)}")
        elif isinstance(value, Iterable):
            # Ordered
            _expand(stack, open_depths, value, value)
        elif isinstance(value, type):
            # `type(value)` is the metaclass, which does not identify the class
            raise TypeError(f"universal unhashable class: {qualname(value)}")
        else:
            raise TypeError(f"universal unhashable type: {type(value)}")

    return UniversalHash(_hash.hexdigest())


_END_OF_NESTING = b")"
_BACK_REFERENCE = b"^"


class _EndOfNesting:
    """Stack item that closes `nested` once all its items are serialized."""

    # Holds `nested` itself and not just its `id`: `uhash` recognizes the values
    # it is expanding by `id` and CPython can allocate a new object at the
    # address of a freed one
    __slots__ = ("nested",)

    def __init__(self, nested: Any) -> None:
        self.nested = nested


# Hashing `[1, [2]]` pops values from the stack until it is empty. Expanding a
# value replaces it by the marker `)` that closes it, followed by its items in
# reverse, so that the items are popped in order and the marker last:
#
#   stack (top last)  popped value  hashed
#   ----------------  ------------  --------------------
#   [1, [2]]          [1, [2]]      "builtins.list"
#   ), [2], 1         1             "builtins.int", "0x1"
#   ), [2]            [2]           "builtins.list"
#   ), ), 2           2             "builtins.int", "0x2"
#   ), )              )             ")"
#   )                 )             ")"
def _expand(
    stack: List[Any], open_depths: Dict[int, int], value: Any, nested: Iterable
) -> None:
    """Schedule the items of `value` for serialization, followed by the item that
    closes `value`.
    """
    # `value` becomes the innermost value being expanded, so its depth is the
    # number of values already being expanded
    open_depths[id(value)] = len(open_depths)
    # The stack is LIFO: the closing item is pushed first so it comes off last
    # and the items are pushed in reverse so they come off in order
    stack.append(_EndOfNesting(value))
    stack.extend(reversed(list(nested)))


def _update_data(_hash, data: bytes) -> None:
    """Hash data of an arbitrary length, prefixed with that length."""
    _hash.update(b"%d:" % len(data))
    _hash.update(data)


def _classhashdata(cls: Type) -> bytes:
    return qualname(cls).encode()


def _multitype_sorted(sequence: Iterable, key=None) -> list:
    """Sort a sequence of which the items are not necessarily comparable."""
    try:
        return sorted(sequence, key=key)
    except TypeError:
        pass

    # The universal hash provides a total order for any set of values
    if key is None:

        def uhash_key(item):
            return str(uhash(item))

    else:

        def uhash_key(item):
            return str(uhash(key(item)))

    return sorted(sequence, key=uhash_key)


class HasUhash(ABC):
    """Base class for objects with a universal hash. Deriving from this class is
    not required to be universally hashable: implementing `__uhash__` is enough.
    """

    @property
    def uhash(self) -> Optional[UniversalHash]:
        _uhash = self.__uhash__()
        if _uhash is None or isinstance(_uhash, UniversalHash):
            return _uhash
        return uhash(self)

    @abstractmethod
    def __uhash__(self) -> Any:
        """The universal hash of the object, a universally hashable value from which
        it is derived, or `None` when the object has no universal hash.
        """
        pass

    def __hash__(self):
        # make it python hashable (to use in sets and dict keys)
        uhash = self.uhash
        if uhash is None:
            return hash(id(self))
        else:
            return hash(uhash)

    def __eq__(self, other):
        return uhash(self) == uhash(other)

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
    MISSING_DATA = missing_data.MISSING_DATA

    def __init__(
        self,
        pre_uhash: Optional[PreUhashTypes] = None,
        instance_nonce: Optional[Any] = None,
    ):
        self.__pre_uhash: Union[None, UniversalHash, HasUhash] = None
        self.__original_pre_uhash: Union[None, UniversalHash, HasUhash] = None
        self.__instance_nonce: Optional[Any] = instance_nonce
        self.__original__instance_nonce: Optional[Any] = instance_nonce
        self.set_uhash_init(pre_uhash=pre_uhash, instance_nonce=instance_nonce)

    def __init_subclass__(subcls, version=None, **kwargs):
        super().__init_subclass__(**kwargs)
        supercls_data = subcls.class_nonce()
        subcls.__VERSION = version
        subcls_data = subcls.class_nonce_data()
        # `_uhash` and not `uhash`: a class nonce contains no registered types
        # and is computed while the module defining the subclass is imported
        subcls.__CLASS_NONCE = str(_uhash((subcls_data, supercls_data)))

    def set_uhash_init(
        self,
        pre_uhash: Optional[PreUhashTypes] = None,
        instance_nonce: Optional[Any] = None,
    ):
        self.__set_pre_uhash(pre_uhash)
        self.__original_pre_uhash = self.__pre_uhash
        self.__instance_nonce = instance_nonce
        self.__original__instance_nonce = instance_nonce

    def __set_pre_uhash(self, pre_uhash):
        if pre_uhash is None:
            self.__pre_uhash = None
        elif isinstance(pre_uhash, (str, bytes)):
            self.__pre_uhash = UniversalHash(pre_uhash)
        elif isinstance(pre_uhash, (UniversalHash, HasUhash)):
            self.__pre_uhash = pre_uhash
        else:
            self.__pre_uhash = uhash(pre_uhash)

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

    def __uhash__(self) -> Optional[UniversalHash]:
        _uhash = self.__pre_uhash
        if _uhash is None:
            data = self._uhash_data()
            if missing_data.is_missing_data(data):
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
        self.__instance_nonce = secrets.randbits(128)

    def undo_randomize(self):
        self.__instance_nonce = self.__original__instance_nonce
