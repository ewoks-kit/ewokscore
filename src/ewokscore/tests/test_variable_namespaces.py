import pytest
from ewokscore import missing_data
from ewokscore.variable import MutableVariableContainer
from ewokscore.variable import VariableContainerNamespace
from ewokscore.variable import ReadOnlyVariableContainerNamespace
from ewokscore.variable import VariableContainerMissingNamespace
from ewokscore.variable import MissingVariableError
from ewokscore.variable import ReadOnlyVariableError


def test_namespace():
    variables = MutableVariableContainer(
        value={"a": None, 0: 1, "c": missing_data.MISSING_DATA}
    )
    namespace = VariableContainerNamespace(variables)
    assert namespace.a is None
    assert namespace["a"] is None
    assert namespace[0] == 1
    assert namespace.c is missing_data.MISSING_DATA
    assert namespace["c"] is missing_data.MISSING_DATA
    with pytest.raises(MissingVariableError):
        namespace.wrong
    with pytest.raises(MissingVariableError):
        namespace["wrong"]
    namespace.a = 10
    assert namespace.a == 10
    namespace["a"] = 20
    assert namespace["a"] == 20


def test_readonly_namespace():
    variables = MutableVariableContainer(
        value={"a": None, 0: 1, "c": missing_data.MISSING_DATA}
    )
    namespace = ReadOnlyVariableContainerNamespace(variables)
    assert namespace.a is None
    assert namespace["a"] is None
    assert namespace[0] == 1
    assert namespace.c is missing_data.MISSING_DATA
    assert namespace["c"] is missing_data.MISSING_DATA
    with pytest.raises(MissingVariableError):
        namespace.wrong
    with pytest.raises(MissingVariableError):
        namespace["wrong"]
    with pytest.raises(ReadOnlyVariableError):
        namespace.a = 10
    with pytest.raises(ReadOnlyVariableError):
        namespace["a"] = 10


def test_missing_namespace():
    variables = MutableVariableContainer(
        value={"a": None, 0: 1, "c": missing_data.MISSING_DATA}
    )
    namespace = VariableContainerMissingNamespace(variables)
    assert namespace.a is False
    assert namespace["a"] is False
    assert namespace[0] is False
    assert namespace.c is True
    assert namespace["c"] is True
    with pytest.raises(MissingVariableError):
        namespace.wrong
    with pytest.raises(MissingVariableError):
        namespace["wrong"]
    with pytest.raises(ReadOnlyVariableError):
        namespace.a = True
    with pytest.raises(ReadOnlyVariableError):
        namespace["a"] = True
