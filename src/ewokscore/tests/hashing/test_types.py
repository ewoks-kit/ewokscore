import datetime
import enum
import itertools
import pathlib
import uuid

import numpy
import pytest

from ... import hashing


def test_hashing_unique():
    unique_values = [
        None,
        "",
        b"",
        "abc",
        b"abc",
        0,
        1,
        0.0,
        1.0,
        numpy.int64(0),
        numpy.int32(1),
    ]
    for v in unique_values:
        assert hashing.uhash(v) == hashing.uhash(v)
    assert len({hashing.uhash(v) for v in unique_values}) == len(unique_values)

    alist = list(unique_values)
    assert hashing.uhash(alist) == hashing.uhash(list(alist))
    assert hashing.uhash(alist) != hashing.uhash(alist[::-1])
    assert hashing.uhash(alist) != hashing.uhash(tuple(alist))
    assert hashing.uhash(alist) != hashing.uhash(set(alist))

    aset = set(unique_values)
    assert hashing.uhash(aset) == hashing.uhash(set(aset))
    assert hashing.uhash(aset) != hashing.uhash(tuple(aset))
    assert hashing.uhash(aset) != hashing.uhash(list(alist))

    andarray = numpy.arange(10)
    assert hashing.uhash(andarray) == hashing.uhash(andarray.copy())
    assert hashing.uhash(andarray) != hashing.uhash(andarray.tolist())

    adict = {i: v for i, v in reversed(list(enumerate(unique_values)))}
    assert hashing.uhash(adict) == hashing.uhash(adict)
    assert hashing.uhash(adict) == hashing.uhash(dict(sorted(adict.items())))


def test_hashing_arbitrary_length_data():
    """Data of an arbitrary length cannot pose as the data around it."""
    assert hashing.uhash([b"A", b"B"]) != hashing.uhash([b"Abuiltins.bytesB"])
    assert hashing.uhash(["A", "B"]) != hashing.uhash(["Abuiltins.strB"])


def test_hashing_uncomparable_keys():
    """Mapping keys and set items need no total order between them."""
    adict = {(1, 2): "a", (1, "b"): "c"}

    assert hashing.uhash(adict) == hashing.uhash(dict(reversed(adict.items())))
    assert hashing.uhash({(1, 2): "a"}) != hashing.uhash({(1, "b"): "a"})

    aset = {(1, 2), (1, "b")}
    assert hashing.uhash(aset) == hashing.uhash(set(aset))


def test_hashing_numbers():
    assert hashing.uhash(1j) != hashing.uhash(complex(1, 0))
    assert hashing.uhash(numpy.bool_(True)) != hashing.uhash(numpy.bool_(False))
    assert hashing.uhash(numpy.datetime64("2026-01-01")) != hashing.uhash(
        numpy.datetime64("2026-01-02")
    )


def test_hashing_bytearray():
    assert hashing.uhash(bytearray(b"ab")) == hashing.uhash(bytearray(b"ab"))
    assert hashing.uhash(bytearray(b"ab")) != hashing.uhash(bytearray(b"ac"))
    assert hashing.uhash(bytearray(b"ab")) != hashing.uhash(b"ab")


def test_hashing_datetime():
    naive = datetime.datetime(2026, 1, 1, 12)
    utc = naive.replace(tzinfo=datetime.timezone.utc)
    plus1 = datetime.datetime(
        2026, 1, 1, 13, tzinfo=datetime.timezone(datetime.timedelta(hours=1))
    )

    # Aware datetimes referring to the same instant are equal
    assert utc == plus1
    assert hashing.uhash(utc) == hashing.uhash(plus1)

    assert hashing.uhash(utc) != hashing.uhash(utc + datetime.timedelta(hours=1))
    assert hashing.uhash(naive) != hashing.uhash(utc)
    assert hashing.uhash(naive) != hashing.uhash(naive.replace(microsecond=1))
    assert hashing.uhash(naive) != hashing.uhash(naive.date())


def test_hashing_date_time_timedelta():
    assert hashing.uhash(datetime.date(2026, 1, 1)) != hashing.uhash(
        datetime.date(2026, 1, 2)
    )
    assert hashing.uhash(datetime.time(12, 30)) != hashing.uhash(datetime.time(12, 31))

    # Equal timedeltas are normalized by the constructor
    assert hashing.uhash(datetime.timedelta(days=1)) == hashing.uhash(
        datetime.timedelta(hours=24)
    )
    assert hashing.uhash(datetime.timedelta(days=1)) != hashing.uhash(
        datetime.timedelta(days=2)
    )


def test_hashing_path_and_uuid():
    assert hashing.uhash(pathlib.PurePosixPath("a//b/")) == hashing.uhash(
        pathlib.PurePosixPath("a/b")
    )
    assert hashing.uhash(pathlib.PurePosixPath("a")) != hashing.uhash(
        pathlib.PurePosixPath("b")
    )

    auuid = uuid.uuid4()
    assert hashing.uhash(auuid) == hashing.uhash(uuid.UUID(str(auuid)))
    assert hashing.uhash(auuid) != hashing.uhash(uuid.uuid4())


def test_hashing_enum():
    class Colour(enum.Enum):
        RED = 1
        BLUE = 2

    class Flags(enum.Flag):
        A = enum.auto()
        B = enum.auto()

    assert hashing.uhash(Colour.RED) == hashing.uhash(Colour(1))
    assert hashing.uhash(Colour.RED) != hashing.uhash(Colour.BLUE)
    assert hashing.uhash(Colour.RED) != hashing.uhash(1)

    # A combination of flags has no name
    assert hashing.uhash(Flags.A | Flags.B) != hashing.uhash(Flags.A)


def test_hashing_ndarray():
    andarray = numpy.arange(6)

    assert hashing.uhash(andarray) == hashing.uhash(andarray.copy())
    assert hashing.uhash(andarray) != hashing.uhash(andarray.tolist())

    # The shape and the data type are part of the universal hash
    assert hashing.uhash(andarray) != hashing.uhash(andarray.reshape(2, 3))
    assert hashing.uhash(andarray) == hashing.uhash(numpy.asfortranarray(andarray))
    assert hashing.uhash(andarray[::2]) == hashing.uhash(andarray[::2].copy())
    assert hashing.uhash(numpy.array([1, 0, 0, 0], dtype="int8")) != hashing.uhash(
        numpy.array([1], dtype="int32")
    )


def test_hashing_ndarray_of_objects():
    def andarray(value):
        return numpy.array([{"a": value}, {"b": 2}], dtype=object)

    # The buffer of an object array contains pointers
    assert hashing.uhash(andarray(1)) == hashing.uhash(andarray(1))
    assert hashing.uhash(andarray(1)) != hashing.uhash(andarray(2))
    assert hashing.uhash(andarray(1)) != hashing.uhash(list(andarray(1)))

    # Zero-dimensional
    assert hashing.uhash(numpy.array({"a": 1}, dtype=object)) == hashing.uhash(
        numpy.array({"a": 1}, dtype=object)
    )

    with pytest.raises(TypeError):
        hashing.uhash(numpy.array([object()], dtype=object))


def test_hashing_iterator():
    """An iterator is consumed by hashing it, so it has no reproducible hash."""
    with pytest.raises(TypeError):
        hashing.uhash(iter([1, 2, 3]))

    with pytest.raises(TypeError):
        hashing.uhash(itertools.count())

    # Views can be iterated more than once
    adict = {"a": 1}
    assert hashing.uhash(adict.keys()) == hashing.uhash(adict.keys())
    assert hashing.uhash(adict.values()) == hashing.uhash(adict.values())


def test_hashing_unhashable():
    class Myclass:
        pass

    with pytest.raises(TypeError, match="Myclass"):
        hashing.uhash(Myclass())

    # A class is not universally hashable and is identified by its own name,
    # not by its metaclass
    with pytest.raises(TypeError, match="Myclass"):
        hashing.uhash(Myclass)

    class MyHashable(hashing.UniversalHashable):
        pass

    with pytest.raises(TypeError, match="MyHashable"):
        hashing.uhash(MyHashable)
