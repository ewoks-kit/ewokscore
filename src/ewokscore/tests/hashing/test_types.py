import numpy

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
