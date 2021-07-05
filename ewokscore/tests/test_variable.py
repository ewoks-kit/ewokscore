from ewokscore.variable import Variable
from ewokscore.variable import MutableVariableContainer

VALUES = [None, True, 10, "string", 10.1, [1, 2, 3], {"1": 1, "2": {"2": [10, 20]}}]


def test_variable_missing_data(varinfo):
    v = Variable(varinfo=varinfo)
    assert not v.has_runtime_value
    assert not v.has_persistent_value
    assert not v.value
    assert not v.uri
    v.dump()
    v.load()
    assert not v.has_runtime_value
    assert not v.has_persistent_value
    assert not v.value
    assert not v.uri
    assert v.value is v.MISSING_DATA
    assert v.value == v.MISSING_DATA


def test_variable_none_uhash():
    for value in VALUES:
        v1 = Variable(value)
        v3 = Variable(uhash=v1)
        v4 = Variable(uhash=v1.uhash)
        assert v1.uhash is None
        assert v3.uhash is None
        assert v4.uhash is None


def test_variable_uhash(varinfo):
    for value in VALUES:
        v1 = Variable(value, varinfo=varinfo)
        v2 = Variable(value, varinfo=varinfo)
        v3 = Variable(uhash=v1, varinfo=varinfo)
        v4 = Variable(uhash=v1.uhash, varinfo=varinfo)
        assert v1.uhash == v2.uhash
        assert v1.uhash == v3.uhash
        assert v1.uhash == v4.uhash
        v1.value = 99999
        assert v1.uhash != v2.uhash
        assert v1.uhash == v3.uhash
        assert v1.uhash != v4.uhash


def test_variable_nonce(varinfo):
    v1 = Variable(9999, varinfo=varinfo)
    v2 = Variable(value=9999, instance_nonce=1, varinfo=varinfo)
    assert v1.uhash != v2.uhash
    assert v1 != v2
    assert v1.value == v2.value
    v2 = Variable(uhash=v1, instance_nonce=1, varinfo=varinfo)
    assert v1.uhash != v2.uhash
    assert v1 != v2
    assert v1.value != v2.value
    v2 = Variable(uhash=v1.uhash, instance_nonce=1, varinfo=varinfo)
    assert v1.uhash != v2.uhash
    assert v1 != v2
    assert v1.value != v2.value


def test_variable_compare(varinfo):
    for value in VALUES:
        v1 = Variable(value, varinfo=varinfo)
        v2 = Variable(value, varinfo=varinfo)
        assert v1 == v2
        assert v1 == value
        assert v2 == value
        v1.value = 99999
        assert v1 != v2
        assert v1 != value
        assert v2 == value


def test_variable_uri(varinfo):
    for value in VALUES:
        v1 = Variable(value, varinfo=varinfo)
        v2 = Variable(value, varinfo=varinfo)
        assert v1.uri is not None
        assert v1.uri == v2.uri
        v1.value = 99999
        assert v1.uri is not None
        assert v1.uri != v2.uri


def test_variable_chain(varinfo):
    v1 = Variable(9999, varinfo=varinfo)
    v2 = Variable(uhash=v1, varinfo=varinfo)
    assert v1 == v1
    v1.value += 1
    assert v1 == v2
    v1.dump()
    assert v1 == v2
    assert v1.value == v2.value
    v1.value += 1
    assert v1 == v2
    assert v1.value != v2.value
    assert not v2.has_persistent_value
    assert v2.has_runtime_value


def test_variable_persistency(varinfo):
    for value in VALUES:
        v1 = Variable(value, varinfo=varinfo)
        v2 = Variable(value, varinfo=varinfo)
        v3 = Variable(uhash=v1.uhash, varinfo=varinfo)
        v4 = Variable(uhash=v2, varinfo=varinfo)

        for v in (v1, v2):
            assert not v.has_persistent_value
            assert v.has_runtime_value

        for v in (v3, v4):
            assert not v.has_persistent_value
            assert not v.has_runtime_value

        v1.dump()

        for v in (v1, v2):
            assert v.has_persistent_value
            assert v.has_runtime_value

        for v in (v3, v4):
            assert v.has_persistent_value
            assert not v.has_runtime_value

        v3.load()
        v4.load()

        for v in (v3, v4):
            assert v.has_persistent_value
            assert v.has_runtime_value


def test_variable_container_uhash(varinfo):
    values = {f"var{i}": value for i, value in enumerate(VALUES, 1)}
    v1 = MutableVariableContainer(value=values, varinfo=varinfo)
    v2 = MutableVariableContainer(value=v1, varinfo=varinfo)
    v3 = MutableVariableContainer(uhash=v1, varinfo=varinfo)
    v4 = MutableVariableContainer(uhash=v1.uhash, varinfo=varinfo)

    v1[next(iter(v1))].value = 9999
    assert v1.uhash == v2.uhash
    assert v1.uhash == v3.uhash
    assert v1.uhash != v4.uhash


def test_variable_container_compare(tmpdir, varinfo):
    values = {f"var{i}": value for i, value in enumerate(VALUES, 1)}
    v1 = MutableVariableContainer(value=values, varinfo=varinfo)
    v2 = MutableVariableContainer(value=v1, varinfo=varinfo)
    v3 = MutableVariableContainer(uhash=v1, varinfo=varinfo)
    v4 = MutableVariableContainer(uhash=v1.uhash, varinfo=varinfo)

    v1.dump()
    v1[next(iter(v1))].value = 9999
    assert v1 == v2
    assert v1 != v3
    assert v1 != v4
    nfiles = len(values) + 1
    assert len(tmpdir.listdir()) == nfiles

    v1.dump()
    assert v1 == v2
    assert v1 == v3
    assert v1 != v4
    assert len(tmpdir.listdir()) == nfiles + 2


def test_variable_container_persistency(tmpdir, varinfo):
    values = {f"var{i}": value for i, value in enumerate(VALUES, 1)}
    v1 = MutableVariableContainer(value=values, varinfo=varinfo)
    v2 = MutableVariableContainer(value=v1, varinfo=varinfo)
    v3 = MutableVariableContainer(uhash=v1, varinfo=varinfo)
    v4 = MutableVariableContainer(uhash=v1.uhash, varinfo=varinfo)

    assert v1.keys() == v2.keys()
    for v in v1.values():
        assert v.uhash != v1.uhash
    for k in v1:
        assert v1[k] is v2[k]

    for v in (v1, v2):
        assert v.container_has_runtime_value
        assert v.has_runtime_value
        assert not v.container_has_persistent_value
        assert not v.has_persistent_value

    for v in (v3, v4):
        assert not v.container_has_runtime_value
        assert not v.has_runtime_value
        assert not v.container_has_persistent_value
        assert not v.has_persistent_value

    assert len(v1) == len(values)
    assert len(v2) == len(values)
    assert len(v3) == 0
    assert len(v4) == 0
    assert v1 == v2
    assert v2 != v3
    assert v2 != v4
    assert len(tmpdir.listdir()) == 0

    v1.dump()
    assert len(tmpdir.listdir()) == len(values) + 1

    for v in (v1, v2):
        assert v.container_has_runtime_value
        assert v.has_runtime_value
        assert v.container_has_persistent_value
        assert v.has_persistent_value

    for v in (v3, v4):
        assert not v.container_has_runtime_value
        assert not v.has_runtime_value
        assert v.container_has_persistent_value
        assert v.has_persistent_value  # calls load
        assert v.container_has_runtime_value

    assert len(v1) == len(values)
    assert len(v2) == len(values)
    assert len(v3) == len(values)
    assert len(v4) == len(values)
    for k in v1:
        assert v1[k] is not v3[k]
    assert v1 == v2 == v3 == v4
    assert len(tmpdir.listdir()) == len(values) + 1
