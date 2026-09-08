import pytest

from ... import hashing


def test_register_uhash():
    """Types that cannot implement `__uhash__` themselves."""

    class Thirdparty:
        def __init__(self, data):
            self.data = data

    with pytest.raises(TypeError):
        hashing.uhash(Thirdparty(1))

    hashing.register_uhash(Thirdparty, lambda obj: obj.data)

    assert hashing.uhash(Thirdparty(1)) == hashing.uhash(Thirdparty(1))
    assert hashing.uhash(Thirdparty(1)) != hashing.uhash(Thirdparty(2))
    assert hashing.uhash(Thirdparty(1)) != hashing.uhash(1)
    assert hashing.uhash([Thirdparty(1)]) != hashing.uhash([Thirdparty(2)])

    class Subclass(Thirdparty):
        pass

    assert hashing.uhash(Subclass(1)) == hashing.uhash(Subclass(1))
    assert hashing.uhash(Subclass(1)) != hashing.uhash(Thirdparty(1))


def test_register_uhash_iterable():
    """Registration takes precedence over hashing a value as an iterable."""

    class Thirdparty:
        def __init__(self, data):
            self.data = data

        def __iter__(self):
            # Does not iterate over the data
            return iter(["name"])

    assert hashing.uhash(Thirdparty(1)) == hashing.uhash(Thirdparty(2))

    hashing.register_uhash(Thirdparty, lambda obj: obj.data)

    assert hashing.uhash(Thirdparty(1)) != hashing.uhash(Thirdparty(2))


def test_uhash_entry_points(monkeypatch):
    """Registration through the `ewoks.hashing` entry point group."""

    class Thirdparty:
        def __init__(self, data):
            self.data = data

    def register():
        hashing.register_uhash(Thirdparty, lambda obj: obj.data)

    monkeypatch.setattr(hashing, "entry_points", _mock_entry_points(register))
    monkeypatch.setattr(hashing, "_LOADED_UHASH_REGISTRATIONS", False)

    assert hashing.uhash(Thirdparty(1)) == hashing.uhash(Thirdparty(1))
    assert hashing.uhash(Thirdparty(1)) != hashing.uhash(Thirdparty(2))


def test_uhash_entry_points_not_loaded_on_import(monkeypatch):
    """Class nonces are hashed while ewokscore is imported."""
    groups = list()
    monkeypatch.setattr(hashing, "entry_points", lambda group: groups.append(group))

    class Test(hashing.UniversalHashable, version=1):
        pass

    assert Test.class_nonce()
    assert not groups


class _MockEntryPoint:
    def __init__(self, obj):
        self._obj = obj

    def load(self):
        return self._obj


def _mock_entry_points(obj):
    def entry_points(group):
        assert group == "ewoks.hashing"
        return [_MockEntryPoint(obj)]

    return entry_points
