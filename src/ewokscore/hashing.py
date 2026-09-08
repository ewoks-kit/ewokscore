"""Universal hashing independent of the current process"""

import hashlib
import secrets
from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import Set
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import Union

import numpy
from ewoksutils.import_utils import qualname

from . import missing_data


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
    if isinstance(value, UniversalHash):
        return value

    # `uhash` serializes a value to a byte stream and hashes that stream with
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

        # Universal hash method to apply to value
        uhash_method = getattr(type(value), "__uhash__", None)

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
        elif isinstance(value, bytes):
            _update_data(_hash, value)
        elif isinstance(value, str):
            _update_data(_hash, value.encode())
        elif isinstance(value, int):
            _hash.update(hex(value).encode())
        elif isinstance(value, float):
            _hash.update(value.hex().encode())
        elif isinstance(value, (numpy.ndarray, numpy.number)):
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
