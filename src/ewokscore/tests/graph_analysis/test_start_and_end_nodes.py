import pytest

from . import _common


def test_start_and_end_nodes():
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "b", "c", "d")],
        [
            {"source": "a", "target": "c"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
        ],
    )

    assert analysis.start_nodes() == {"a", "b"}
    assert analysis.end_nodes() == {"d"}


def test_start_nodes_with_force_start_node():
    analysis = _common.analysis(
        [_common.node("a"), _common.node("b", force_start_node=True)],
        [{"source": "a", "target": "b"}],
    )

    assert analysis.start_nodes() == {"a", "b"}


def test_start_nodes_without_node_without_predecessors():
    """Fall back to the nodes that have all required inputs statically defined."""
    analysis = _common.analysis(
        [
            _common.class_node("ready", default_inputs=[{"name": "a", "value": 1}]),
            _common.class_node("waiting"),
        ],
        [
            {"source": "ready", "target": "waiting"},
            {"source": "waiting", "target": "ready", "conditions": _common.TRUE},
        ],
    )

    assert analysis.start_nodes() == {"ready"}


def test_end_nodes_without_node_without_successors():
    """Fall back to the nodes with uncovered conditions."""
    analysis = _common.analysis(
        [_common.node("a"), _common.node("b")],
        [
            {"source": "a", "target": "b", "conditions": _common.TRUE},
            {"source": "b", "target": "a", "conditions": _common.TRUE},
        ],
    )

    assert analysis.end_nodes() == {"a", "b"}


def test_start_and_end_nodes_are_copies():
    analysis = _common.analysis(
        [_common.node("a"), _common.node("b")], _common.chain("a", "b")
    )

    start_nodes = analysis.start_nodes()
    end_nodes = analysis.end_nodes()

    with pytest.raises(AttributeError):
        start_nodes.add("injected")
    with pytest.raises(AttributeError):
        end_nodes.end_nodes().add("injected")

    assert analysis.start_nodes() == {"a"}
    assert analysis.end_nodes() == {"b"}
