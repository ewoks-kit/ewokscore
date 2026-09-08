from ... import hashing


def test_hashing_nesting():
    """Values that expand to the same flat sequence must not collide."""
    assert hashing.uhash([1, [2]]) != hashing.uhash([[1, 2]])
    assert hashing.uhash([[1, 2], []]) != hashing.uhash([[[1, 2]]])
    assert hashing.uhash([[1], [2]]) != hashing.uhash([[1, 2], []])
    assert hashing.uhash([[1], [2]]) != hashing.uhash([[1, [2]]])
    assert hashing.uhash({"a": [1, 2]}) != hashing.uhash({"a": [1], "b": [2]})

    shared = [1]
    assert hashing.uhash([shared, shared]) == hashing.uhash([[1], [1]])


def test_hashing_deep_nesting():
    """Nesting deeper than the python recursion limit is supported."""
    value = deepest = list()
    for _ in range(20000):
        nested = list()
        deepest.append(nested)
        deepest = nested

    assert hashing.uhash(value) == hashing.uhash(value)


def test_hashing_circular_reference():
    def selflist(item):
        alist = [item]
        alist.append(alist)
        return alist

    def selfdict(item):
        adict = {"item": item}
        adict["self"] = adict
        return adict

    assert hashing.uhash(selflist(1)) == hashing.uhash(selflist(1))
    assert hashing.uhash(selflist(1)) != hashing.uhash(selflist(2))
    assert hashing.uhash(selfdict(1)) == hashing.uhash(selfdict(1))
    assert hashing.uhash(selfdict(1)) != hashing.uhash(selfdict(2))
    assert hashing.uhash(selflist(1)) != hashing.uhash(selfdict(1))

    # The value a circular reference points to matters
    inner = list()
    inner.append(inner)
    refers_to_inner = [inner]

    refers_to_outer = list()
    refers_to_outer.append([refers_to_outer])

    assert hashing.uhash(refers_to_inner) != hashing.uhash(refers_to_outer)
