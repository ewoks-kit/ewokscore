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

    adict = {-i: v for i, v in enumerate(unique_values, 1)}
    assert hashing.uhash(adict) == hashing.uhash(adict)
    assert hashing.uhash(adict) == hashing.uhash(dict(sorted(adict.items())))


def test_hashing_arbitrary_length_data():
    """Data of an arbitrary length cannot pose as the data around it."""
    assert hashing.uhash([b"A", b"B"]) != hashing.uhash([b"Abuiltins.bytesB"])
    assert hashing.uhash(["A", "B"]) != hashing.uhash(["Abuiltins.strB"])


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
