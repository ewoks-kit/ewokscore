"""
Serialized objects with custom serialization for certain dictionary keys.

Converters are selected by the path of a value, where a `"*"` in the pattern
matches any dictionary key or sequence index. Only the values of dictionary keys
are converted: a pattern ending on a sequence index has no effect.
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

from .utils import types
from .utils.traversal import Traversal

_WILDCARD = "*"

_NO_PATTERNS: Tuple["_PatternNode", ...] = ()


class _PatternNode:
    """One element of the converter path patterns, with all patterns sharing the
    same prefix stored under the same node.

    Matching a path against `n` patterns of length `l` costs `n * l` comparisons.
    With the patterns in a trie it costs one dictionary lookup per path element.
    More importantly, a key that leaves the trie tells us that no pattern can
    match anything below it, so that part of the object needs no conversion.
    """

    __slots__ = ("children", "wildcard", "converter")

    def __init__(self) -> None:
        self.children: Dict[types.KeyType, "_PatternNode"] = dict()
        self.wildcard: Optional["_PatternNode"] = None
        self.converter: Optional[types.ConverterType] = None

    def add(self, pattern: types.PathPattern, converter: types.ConverterType) -> None:
        """Store the converter of the values a path pattern points to."""
        node = self
        for key in pattern:
            if key == _WILDCARD:
                if node.wildcard is None:
                    node.wildcard = _PatternNode()
                node = node.wildcard
            else:
                child = node.children.get(key)
                if child is None:
                    child = node.children[key] = _PatternNode()
                node = child
        node.converter = converter


def _pattern_trie(
    converters: Dict[types.PathPattern, types.ConverterType],
) -> _PatternNode:
    """The root of the trie holding all converter path patterns."""
    root = _PatternNode()
    for pattern, converter in converters.items():
        root.add(pattern, converter)
    return root


def _descend(
    nodes: Sequence[_PatternNode], key: types.KeyType
) -> Tuple[Optional[types.ConverterType], Sequence[_PatternNode]]:
    """The converter for the value at `key` and the pattern nodes continuing below it.

    A key can continue more than one pattern, an exact match and a wildcard for
    example, so more than one node can remain. An exact match provides the
    converter before a wildcard does. Nodes that end their pattern here do not
    remain: nothing below them can match.
    """
    converter = None
    remaining: List[_PatternNode] = []

    for node in nodes:
        for child in (node.children.get(key), node.wildcard):
            if child is None:
                continue
            if converter is None:
                converter = child.converter
            if child.children or child.wildcard is not None:
                remaining.append(child)

    if not remaining:
        return converter, _NO_PATTERNS
    return converter, remaining


def _convert(obj: Any, converters: Dict[types.PathPattern, types.ConverterType]) -> Any:
    """Rebuild `obj`, replacing every value whose path matches one of the
    `converters` path patterns by its converted value.

    Values that no pattern can reach into are inserted as-is rather than being
    rebuilt: they cannot change, and copying them is arbitrarily expensive since
    node inputs and outputs hold user data. The root is always a new container,
    so a caller can add to the result without modifying `obj`.
    """
    # The traversal state is the set of pattern nodes still matching
    t = Traversal(obj, state=(_pattern_trie(converters),))

    while t.next():
        current = t.current
        patterns = t.state

        # --- dict ---
        if isinstance(current, dict):
            converted: Any = dict()
            t.assign(converted)
            for key, value in current.items():
                converter, below = _descend(patterns, key)
                if converter is not None:
                    converted[key] = converter(value)
                elif below:
                    # Reserve the position of the key, filled in when popped
                    converted[key] = None
                    t.append(converted, key, value, below)
                else:
                    converted[key] = value
            continue

        # --- list ---
        if isinstance(current, list):
            converted = [None] * len(current)
            t.assign(converted)
            for index, value in enumerate(current):
                # Converters apply to dictionary keys only, so the converter of a
                # pattern ending on a sequence index is ignored. A wildcard still
                # matches the index to reach the dictionaries below it.
                _, below = _descend(patterns, index)
                if below:
                    t.append(converted, index, value, below)
                else:
                    converted[index] = value
            continue

        # --- passthrough ---
        t.assign(current)

    return t.result


def pre_serialize(
    obj: Any,
    item_serializers: Optional[Dict[types.Path, types.ConverterType]] = None,
) -> Any:
    """
    :param obj: object to serialize
    :param item_serializers: paths to nested dict/list item with associated custom value serialization
    """
    if not item_serializers:
        return obj
    return _convert(obj, item_serializers)


def post_deserialize(
    obj: Any,
    item_deserializers: Optional[Dict[types.Path, types.ConverterType]] = None,
) -> Any:
    """
    :param obj: object to deserialize
    :param item_deserializers: paths to nested dict/list item with associated custom value deserialization
    """
    if not item_deserializers:
        return obj
    return _convert(obj, item_deserializers)
