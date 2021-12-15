import gc
import pytest
from contextlib import contextmanager
from ewokscore.variable import Variable
from ewokscore.variable import MutableVariableContainer

VALUES = [None, True, 10, "string", 10.1, [1, 2, 3], {"1": 1, "2": {"2": [10, 20]}}]


def test_variable_no_value(varinfo):
    var = Variable(varinfo=varinfo)
    assert_variable_no_value(var)


def test_variable_container_no_value(varinfo):
    var = MutableVariableContainer(varinfo=varinfo)
    assert_variable_no_value(var)


def test_variable_container_wrong_value():
    with pytest.raises(TypeError):
        MutableVariableContainer(value=[1, 2])


def assert_variable_no_value(var):
    assert not var.has_runtime_value
    assert not var.has_persistent_value
    assert not var.value
    assert not var.data_uri
    var.dump()
    var.load()
    assert not var.has_runtime_value
    assert not var.has_persistent_value
    assert not var.value
    assert not var.data_uri
    assert var.value is var.MISSING_DATA
    assert var.value == var.MISSING_DATA


@pytest.mark.parametrize("value", VALUES)
def test_variable_references(value, varinfo):
    var = Variable(value, varinfo=varinfo)
    references = {
        "same_instance": var,
        "same_value": Variable(value, varinfo=varinfo),
        "ref_uhashable": Variable(pre_uhash=var, varinfo=varinfo),
        "ref_uhash": Variable(pre_uhash=var.uhash, varinfo=varinfo),
        "ref_proxy": Variable(data_proxy=var.data_proxy),
        "ref_uri": Variable(data_uri=var.data_uri),
    }
    assert_variable(var, **references)


def test_variable_container_references(varinfo):
    value = {f"var{i}": value for i, value in enumerate(VALUES, 1)}
    var = MutableVariableContainer(value=value, varinfo=varinfo)
    references = {
        "same_instance": var,
        "same_value": MutableVariableContainer(value=value, varinfo=varinfo),
        "ref_uhashable": MutableVariableContainer(pre_uhash=var, varinfo=varinfo),
        "ref_uhash": MutableVariableContainer(pre_uhash=var.uhash, varinfo=varinfo),
        "ref_proxy": MutableVariableContainer(data_proxy=var.data_proxy),
        "ref_uri": MutableVariableContainer(data_uri=var.data_uri),
        "ref_same_variables": MutableVariableContainer(value=var, varinfo=varinfo),
    }
    assert_variable(var, **references)


def assert_variable(var, **references):
    assert_variable_compare(var, **references)
    assert_variable_uhash(var, **references)
    assert_variable_uri(var, **references)
    assert_variable_data_proxy(var, **references)
    assert_variable_value(var, **references)
    assert_variable_value_status(var, **references)
    var.dump()
    assert_variable_compare(var, **references)
    assert_variable_uhash(var, **references)
    assert_variable_uri(var, **references)
    assert_variable_data_proxy(var, **references)
    assert_persisted_variable_value(var, **references)
    assert_persisted_variable_value_status(var, **references)


def assert_variable_uhash(var, **references):
    for name, var_ref in references.items():
        assert var.uhash == var_ref.uhash, name
    with change_value(var):
        for name, var_ref in references.items():
            if name in ("same_instance", "ref_uhashable", "ref_same_variables"):
                assert var.uhash == var_ref.uhash, name
            else:
                assert var.uhash != var_ref.uhash, name


def assert_variable_compare(var, **references):
    for name, var_ref in references.items():
        try:
            assert var == var_ref, name
        except AssertionError:
            var == var_ref
            raise
    with change_value(var):
        for name, var_ref in references.items():
            if name in ("same_instance", "ref_uhashable", "ref_same_variables"):
                assert var == var_ref, name
            else:
                assert var != var_ref, name


def assert_variable_data_proxy(var, **references):
    for name, var_ref in references.items():
        assert var.data_proxy == var_ref.data_proxy, name
    with change_value(var):
        for name, var_ref in references.items():
            if name in (
                "same_instance",
                "ref_uhashable",
                "ref_same_variables",
                "ref_proxy",
            ):
                assert var.data_proxy == var_ref.data_proxy, name
            else:
                assert var.data_proxy != var_ref.data_proxy, name


def assert_variable_uri(var, **references):
    for name, var_ref in references.items():
        assert var.data_uri == var_ref.data_uri, name
    with change_value(var):
        for name, var_ref in references.items():
            if name in (
                "same_instance",
                "ref_uhashable",
                "ref_same_variables",
                "ref_proxy",
            ):
                assert var.data_uri == var_ref.data_uri, name
            else:
                assert var.data_uri != var_ref.data_uri, name


def assert_variable_value(var, **references):
    # Side effect: variable will have runtime values (lazy loading in the `value` property)
    for name, var_ref in references.items():
        if name in ("same_instance", "same_value", "ref_same_variables"):
            assert var.value == var_ref.value, name
        else:
            assert var.value != var_ref.value, name
    with change_value(var):
        for name, var_ref in references.items():
            if name in ("same_instance", "ref_same_variables"):
                assert var.value == var_ref.value, name
            else:
                assert var.value != var_ref.value, name


def assert_persisted_variable_value(var, **references):
    # Assumption: values have been loaded
    for name, var_ref in references.items():
        assert var.value == var_ref.value, name
    with change_value(var):
        for name, var_ref in references.items():
            if name in ("same_instance", "ref_same_variables"):
                assert var.value == var_ref.value, name
            else:
                assert var.value != var_ref.value, name


def assert_variable_value_status(var, **references):
    # Assumption: values have not been loaded
    is_container = isinstance(var, MutableVariableContainer)

    for name, var_ref in references.items():
        if name in ("same_instance", "same_value", "ref_same_variables"):
            if is_container:
                assert not var_ref.container_has_persistent_value, name
                assert var_ref.container_has_runtime_value, name
            assert not var_ref.has_persistent_value, name
            assert var_ref.has_runtime_value, name
        else:
            if is_container:
                assert not var_ref.container_has_persistent_value, name
                assert not var_ref.container_has_runtime_value, name
            assert not var_ref.has_persistent_value, name
            assert not var_ref.has_runtime_value, name


def assert_persisted_variable_value_status(var, **references):
    # Assumption: values have been loaded
    # Side effect: container variables will have runtime values (explicit loading)
    is_container = isinstance(var, MutableVariableContainer)

    for name, var_ref in references.items():
        if is_container:
            assert var_ref.container_has_persistent_value, name
            assert var_ref.container_has_runtime_value, name
        else:
            assert var_ref.has_persistent_value, name
            assert var_ref.has_runtime_value, name
        if is_container:
            if name in ("same_instance", "same_value", "ref_same_variables"):
                assert var_ref.has_runtime_value, name
            else:
                assert not var_ref.has_runtime_value, name
                for sub_var in var_ref.value.values():
                    sub_var.load()
                assert var_ref.has_runtime_value, name


@contextmanager
def change_value(var):
    if isinstance(var, MutableVariableContainer):
        name = next(iter(var))
        keep = var[name].value
        var[name].value = 9999
    else:
        keep = var.value
        var.value = 9999
    try:
        yield
    finally:
        if isinstance(var, MutableVariableContainer):
            var[name].value = keep
        else:
            var.value = keep


def test_variable_nonce(varinfo):
    v1 = Variable(9999, varinfo=varinfo)
    v2 = Variable(value=9999, instance_nonce=1, varinfo=varinfo)
    assert v1.uhash != v2.uhash
    assert v1 != v2
    assert v1.value == v2.value
    v2 = Variable(pre_uhash=v1, instance_nonce=1, varinfo=varinfo)
    assert v1.uhash != v2.uhash
    assert v1 != v2
    assert v1.value != v2.value
    v2 = Variable(pre_uhash=v1.uhash, instance_nonce=1, varinfo=varinfo)
    assert v1.uhash != v2.uhash
    assert v1 != v2
    assert v1.value != v2.value


@pytest.mark.parametrize("scheme", ("json", "nexus"))
@pytest.mark.parametrize("root_uri_type", ("directory", "filename", "path_in_file"))
def test_variable_container_metadata(scheme, root_uri_type, tmpdir):
    if scheme == "nexus":
        extension = ".nx"
    else:
        extension = ".json"

    if root_uri_type == "path_in_file":
        root_uri = tmpdir / f"dataset_name{extension}::/scan_name"
    elif root_uri_type == "filename":
        root_uri = tmpdir / f"dataset_name{extension}"
    elif root_uri_type == "directory":
        root_uri = tmpdir
    varinfo = {"root_uri": str(root_uri), "scheme": scheme}

    values = {f"var{i}": i for i in range(3)}
    container = MutableVariableContainer(value=values, varinfo=varinfo)
    container.metadata["myvalue"] = 999
    container["var1"].metadata["myvalue"] = 888
    container.dump()

    # Common ways to receive data
    ref_uri = MutableVariableContainer(data_uri=container.data_uri)
    ref_transfer_data = MutableVariableContainer(
        value=container.variable_transfer_data, varinfo={"has_data_proxy": True}
    )
    assert ref_uri.uhash == container.uhash
    assert ref_transfer_data.uhash == container.uhash

    # Check data
    assert container.variable_values == ref_transfer_data.variable_values
    assert container.variable_transfer_data == ref_transfer_data.variable_transfer_data
    assert container.variable_values == ref_uri.variable_values
    assert container.variable_transfer_data == ref_uri.variable_transfer_data

    # Check metadata
    if scheme == "nexus":
        if root_uri_type == "path_in_file":
            assert ref_uri.metadata["@NX_class"] == "NXcollection"
        else:
            assert ref_uri.metadata["@NX_class"] == "NXprocess"

    assert ref_uri.metadata["myvalue"] == 999

    if scheme == "nexus":
        assert ref_uri["var1"].metadata["@NX_class"] == "NXcollection"
    assert ref_uri["var1"].metadata["myvalue"] == 888


def test_variable_cleanup_references():
    obj = [0, 1, 2]
    nref_start = len(gc.get_referrers(obj))
    var1 = Variable(obj)
    var2 = Variable(pre_uhash=var1)
    uhash = var1.uhash
    assert uhash == var2.uhash
    assert len(gc.get_referrers(obj)) > nref_start

    del var1
    while gc.collect():
        pass
    assert len(gc.get_referrers(obj)) > nref_start

    var2.cleanup_references()
    while gc.collect():
        pass
    assert len(gc.get_referrers(obj)) == nref_start

    assert uhash == var2.uhash


def test_variable_container_cleanup_references():
    obj = [0, 1, 2]
    nref_start = len(gc.get_referrers(obj))
    var1 = MutableVariableContainer({"myvar": obj})
    var2 = MutableVariableContainer(pre_uhash=var1)
    uhash = var1.uhash
    assert uhash == var2.uhash

    del var1
    while gc.collect():
        pass
    assert len(gc.get_referrers(obj)) > nref_start

    var2.cleanup_references()
    while gc.collect():
        pass
    assert len(gc.get_referrers(obj)) == nref_start

    assert uhash == var2.uhash
