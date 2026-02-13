import gc
import numpy
from ewokscore import hashing


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


def test_pre_uhash():
    class Test(hashing.UniversalHashable, version=1):
        def __init__(self, data, **kw):
            self.data = data
            super().__init__(**kw)

        def _uhash_data(self):
            return self.data

    a = Test(1, pre_uhash=None, instance_nonce=10)
    b = Test(2, pre_uhash=a)  # keeps a reference
    c = Test(3, pre_uhash=a.uhash)  # no reference

    assert a.uhash == b.uhash
    assert a.uhash == c.uhash

    a.data = 3

    assert a.uhash == b.uhash
    assert a.uhash != c.uhash


def test_versioning():
    def create_classes(vparent=None, vchild=None):
        class Mixin1:
            pass

        class Mixin2:
            pass

        class Parent(Mixin1, hashing.UniversalHashable, Mixin2, version=vparent):
            pass

        class Child(Parent, version=vchild):
            pass

        return Parent.class_nonce(), Child.class_nonce()

    vparent1, vchild1 = create_classes()
    vparent2, vchild2 = create_classes(vparent=1)
    vparent3, vchild3 = create_classes(vchild=1)
    vparent4, vchild4 = create_classes(vparent=1, vchild=1)

    assert vparent1 != vchild1
    assert vparent2 != vchild2
    assert vparent3 != vchild3
    assert vparent4 != vchild4

    assert vparent1 != vparent2
    assert vparent1 == vparent3
    assert vparent2 == vparent4

    assert vchild1 != vchild2
    assert vchild2 != vchild3
    assert vchild3 != vchild4


def test_uhash_fixing():
    class Test(hashing.UniversalHashable):
        def __init__(self, data):
            self.data = data
            super().__init__()

        def _uhash_data(self):
            return self.data

    data = [0, 1, 2]
    var = Test(data)

    uhash1 = uhash1org = var.uhash
    data[0] += 1
    uhash2 = var.uhash
    assert uhash1 != uhash2

    uhash1 = var.uhash
    var.fix_uhash()
    uhash2 = var.uhash
    data[0] += 1
    uhash3 = var.uhash
    assert uhash1 == uhash2
    assert uhash1 == uhash3

    uhash1 = var.uhash
    var.undo_fix_uhash()
    uhash2 = var.uhash
    assert uhash1 != uhash2

    data[0] = 0
    uhash = var.uhash
    assert uhash1org == uhash


def test_hashable_cleanup_references():
    class Myclass(hashing.UniversalHashable):
        def __init__(self, data, **kw):
            self.data = data
            super().__init__(**kw)

        def _uhash_data(self):
            return self.data

    obj1 = Myclass(10)
    nref_start = len(gc.get_referrers(obj1))
    obj2 = Myclass(10, pre_uhash=obj1)
    assert len(gc.get_referrers(obj1)) > nref_start

    obj1.data += 1
    assert obj1.uhash == obj2.uhash

    obj2.cleanup_references()
    while gc.collect():
        pass
    assert len(gc.get_referrers(obj1)) == nref_start
    assert obj1.uhash == obj2.uhash

    obj1.data += 1
    assert obj1.uhash != obj2.uhash
