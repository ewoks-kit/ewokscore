import itertools
import pytest
from ewokscore.variable import Variable
from ewokscore.variable import MutableVariableContainer

VALUES = [None, True, 10, "string", 10.1, [1, 2, 3], {"1": 1, "2": {"2": [10, 20]}}]


def test_variable_missing_data(varinfo):
    v = Variable(varinfo=varinfo)
    assert not v.has_runtime_value
    assert not v.has_persistent_value
    assert not v.value
    assert not v.data_proxy.uri
    v.dump()
    v.load()
    assert not v.has_runtime_value
    assert not v.has_persistent_value
    assert not v.value
    assert not v.data_proxy.uri
    assert v.value is v.MISSING_DATA
    assert v.value == v.MISSING_DATA


@pytest.mark.parametrize("value", VALUES)
def test_variable_none_uhash(value):
    v1 = Variable(value)
    v3 = Variable(uhash=v1)
    v4 = Variable(uhash=v1.uhash)
    assert v1.uhash is None
    assert v3.uhash is None
    assert v4.uhash is None


@pytest.mark.parametrize("value", VALUES)
def test_variable_uhash(value, varinfo):
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


@pytest.mark.parametrize("value", VALUES)
def test_variable_compare(value, varinfo):
    v1 = Variable(value, varinfo=varinfo)
    v2 = Variable(value, varinfo=varinfo)
    assert v1 == v2
    assert v1 == value
    assert v2 == value
    v1.value = 99999
    assert v1 != v2
    assert v1 != value
    assert v2 == value


@pytest.mark.parametrize("value", VALUES)
def test_variable_uri(value, varinfo):
    v1 = Variable(value, varinfo=varinfo)
    v2 = Variable(value, varinfo=varinfo)
    assert v1.data_proxy.uri is not None
    assert v1.data_proxy.uri == v2.data_proxy.uri
    v1.value = 99999
    assert v1.data_proxy.uri is not None
    assert v1.data_proxy.uri != v2.data_proxy.uri


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


@pytest.mark.parametrize("value", VALUES)
def test_variable_persistence(value, varinfo):
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


def test_variable_container_persistence(tmpdir, varinfo):
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


@pytest.mark.parametrize(
    "scheme,full",
    itertools.product(["json", "nexus"], [False, True]),
)
def test_variable_container_dump(scheme, full, tmpdir):
    if full and scheme == "nexus":
        root_uri = str(tmpdir / "dataset.nx") + "::/scan"
    else:
        root_uri = str(tmpdir)
    varinfo = {"root_uri": root_uri, "scheme": scheme}

    values = {f"var{i}": i for i in range(3)}
    v1 = MutableVariableContainer(value=values, varinfo=varinfo)
    v2 = MutableVariableContainer(uhash=v1.uhash, varinfo=varinfo)
    if scheme == "nexus":
        v1.metadata["myvalue"] = 999
    else:
        assert v1.metadata is None
    v1.dump()

    if scheme == "nexus":
        assert len(tmpdir.listdir()) == 1
    else:
        assert len(tmpdir.listdir()) == len(values) + 1
    assert v1.uhash == v2.uhash
    assert v1.variable_uhashes == v2.variable_uhashes
    assert v1.data_proxy.uri == v2.data_proxy.uri
    assert v1.variable_uris == v2.variable_uris
    urihashes1 = {k: v.uhash for k, v in v1.variable_uris.items()}
    urihashes2 = {k: v.uhash for k, v in v2.variable_uris.items()}
    assert urihashes1 == urihashes2
    assert v1.variable_transfer_data == v2.variable_transfer_data
    assert v1.variable_values == v2.variable_values
    if scheme == "nexus":
        assert v1.metadata_proxy.uri == v2.metadata_proxy.uri
        adict = v2.metadata_proxy.load()
        assert adict["@NX_class"] == "NXprocess"
        assert adict["myvalue"] == 999
    else:
        assert v1.metadata_proxy is None
        assert v2.metadata_proxy is None
