import pytest

from ... import hashing


def test_has_uhash_is_abstract():
    class Myclass(hashing.HasUhash):
        pass

    with pytest.raises(TypeError):
        Myclass()


def test_uhash_method():
    """A class becomes universally hashable by implementing `__uhash__`,
    without deriving from `HasUhash`.
    """

    class Myclass:
        def __init__(self, data):
            self.data = data

        def __uhash__(self):
            return self.data

    assert hashing.uhash(Myclass(1)) == hashing.uhash(Myclass(1))
    assert hashing.uhash(Myclass(1)) != hashing.uhash(Myclass(2))
    assert hashing.uhash(Myclass(1)) != hashing.uhash(1)
    assert hashing.uhash([Myclass(1)]) != hashing.uhash([1])

    # The class itself is not universally hashable
    with pytest.raises(TypeError, match="Myclass"):
        hashing.uhash(Myclass)


def test_uhash_method_returns_uhash():
    class Myclass:
        def __init__(self, data):
            self.data = hashing.uhash(data)

        def __uhash__(self):
            return self.data

    obj = Myclass(1)
    assert hashing.uhash(obj) == obj.__uhash__()
    assert hashing.uhash([obj]) != hashing.uhash([obj.__uhash__()])


def test_has_uhash_returns_hashable_value():
    """`__uhash__` can return a universally hashable value instead of a `UniversalHash`."""

    class Myclass(hashing.HasUhash):
        def __init__(self, data):
            self.data = data

        def __uhash__(self):
            return self.data

    obj = Myclass([1, 2])
    assert isinstance(obj.uhash, hashing.UniversalHash)
    assert obj.uhash == hashing.uhash(obj)
    assert obj.uhash != Myclass([2, 1]).uhash
    assert obj == obj.uhash

    obj.data = None
    assert obj.uhash is None


def test_hashable_equality():
    class Test(hashing.UniversalHashable, version=1):
        def __init__(self, data, **kw):
            self.data = data
            super().__init__(**kw)

        def _uhash_data(self):
            return self.data

    a = Test(1)
    b = Test(1)
    c = Test(2)

    assert a == b
    assert a != c
    assert a == a.uhash
    assert a != c.uhash
    assert a != "not a hashable"
