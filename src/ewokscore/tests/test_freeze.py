import pickle

import networkx
import pytest

from ..graph._freeze import FrozenDiGraph
from ..graph._freeze import _FrozenDict
from ..graph._freeze import _NodeAttrs


def test_frozen_dict_is_read_only():
    d = _FrozenDict({"a": 1})

    with pytest.raises(TypeError):
        d["a"] = 2
    with pytest.raises(TypeError):
        d["b"] = 2
    with pytest.raises(TypeError):
        del d["a"]
    with pytest.raises(TypeError):
        d.clear()
    with pytest.raises(TypeError):
        d.pop("a")
    with pytest.raises(TypeError):
        d.popitem()
    with pytest.raises(TypeError):
        d.setdefault("b", 2)
    with pytest.raises(TypeError):
        d.update({"a": 2})
    assert d == {"a": 1}


def test_node_attrs_default_inputs_is_mutable():
    n = _NodeAttrs({"task_type": "method", "default_inputs": []})

    n["default_inputs"] = [{"name": "a", "value": 1}]
    assert n["default_inputs"] == [{"name": "a", "value": 1}]

    # Every other key stays read-only
    with pytest.raises(TypeError):
        n["task_type"] = "other"
    with pytest.raises(TypeError):
        n["new_key"] = "value"

    # `default_inputs` can only be reassigned, not removed or bulk-updated
    with pytest.raises(TypeError):
        del n["default_inputs"]
    with pytest.raises(TypeError):
        n.update({"default_inputs": []})


def test_frozen_dict_pickle_roundtrip():
    original = _FrozenDict({"a": 1, "b": 2})
    restored = pickle.loads(pickle.dumps(original))  # noqa: S301

    assert restored == original
    assert isinstance(restored, _FrozenDict)
    with pytest.raises(TypeError):
        restored["a"] = 3


def test_node_attrs_pickle_roundtrip():
    original = _NodeAttrs({"task_type": "method", "default_inputs": []})
    restored = pickle.loads(pickle.dumps(original))  # noqa: S301

    assert restored == original
    assert isinstance(restored, _NodeAttrs)
    restored["default_inputs"] = [{"name": "a", "value": 1}]
    with pytest.raises(TypeError):
        restored["task_type"] = "other"


def test_frozen_digraph_pickle_roundtrip():
    graph = networkx.DiGraph(id="test")
    graph.add_node("source", task_type="method")
    graph.add_node("target", task_type="method")
    graph.add_edge("source", "target", data_mapping=[])

    original = FrozenDiGraph(graph)
    restored = pickle.loads(pickle.dumps(original))  # noqa: S301

    assert isinstance(restored, FrozenDiGraph)
    assert dict(restored.graph) == dict(original.graph)
    assert dict(restored.nodes(data=True)) == dict(original.nodes(data=True))
    assert dict(restored.edges) == dict(original.edges)

    assert isinstance(restored.graph, _FrozenDict)
    with pytest.raises(TypeError):
        restored.graph["id"] = "other"
    with pytest.raises(TypeError):
        restored.nodes["source"]["task_type"] = "other"
    with pytest.raises(TypeError):
        restored.edges["source", "target"]["data_mapping"] = None
    with pytest.raises(networkx.NetworkXError):
        restored.add_node("new")
