from typing import Callable
from typing import List
from typing import Optional

import pytest

from ... import hashing


@pytest.fixture
def mock_uhash_entry_points(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[Optional[Callable[[], None]]], List[str]]:
    """Mock the `ewoks.hashing` entry point group, not loaded yet. Mocking
    returns the list in which the requested groups are recorded.
    """

    def mock(register: Optional[Callable[[], None]] = None) -> List[str]:
        groups: List[str] = list()

        def _mock_entry_points(group: str) -> List["_MockEntryPoint"]:
            groups.append(group)
            if register is None:
                return list()
            return [_MockEntryPoint(register)]

        monkeypatch.setattr(hashing, "entry_points", _mock_entry_points)
        monkeypatch.setattr(hashing, "_LOADED_UHASH_REGISTRATIONS", False)
        return groups

    return mock


class _MockEntryPoint:
    def __init__(self, obj: Callable[[], None]) -> None:
        self._obj = obj

    def load(self) -> Callable[[], None]:
        return self._obj


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


def test_uhash_entry_points(mock_uhash_entry_points):
    """Registration through the `ewoks.hashing` entry point group."""

    class Thirdparty:
        def __init__(self, data):
            self.data = data

    def register():
        hashing.register_uhash(Thirdparty, lambda obj: obj.data)

    groups = mock_uhash_entry_points(register)

    assert hashing.uhash(Thirdparty(1)) == hashing.uhash(Thirdparty(1))
    assert hashing.uhash(Thirdparty(1)) != hashing.uhash(Thirdparty(2))
    assert groups == ["ewoks.hashing"]


def test_uhash_entry_points_not_loaded_on_import(mock_uhash_entry_points):
    """Class nonces are hashed while ewokscore is imported, so hashing them
    must not load the `ewoks.hashing` entry points (circular import).
    """
    groups = mock_uhash_entry_points()

    class Test(hashing.UniversalHashable, version=1):
        pass

    assert Test.class_nonce()
    assert not groups
