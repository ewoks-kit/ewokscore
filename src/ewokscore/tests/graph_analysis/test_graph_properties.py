import pytest

from . import _common


def test_graph_is_cyclic():
    assert not _common.analysis(
        [_common.node("a"), _common.node("b")], _common.chain("a", "b")
    ).graph_is_cyclic()

    cyclic = _common.analysis(
        [_common.node("a"), _common.node("b")],
        [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "a", "conditions": _common.TRUE},
        ],
    )
    assert cyclic.graph_is_cyclic()

    self_loop = _common.analysis(
        [_common.node("a")],
        [{"source": "a", "target": "a", "conditions": _common.TRUE}],
    )
    assert self_loop.graph_is_cyclic()


def test_graph_has_conditional_links():
    assert not _common.analysis(
        [_common.node("a"), _common.node("b")], _common.chain("a", "b")
    ).graph_has_conditional_links()

    assert _common.analysis(
        [_common.node("a"), _common.node("b")],
        [{"source": "a", "target": "b", "conditions": _common.TRUE}],
    ).graph_has_conditional_links()

    assert _common.analysis(
        [_common.node("a"), _common.node("b")],
        [{"source": "a", "target": "b", "on_error": True}],
    ).graph_has_conditional_links()

    # An empty condition list is not a condition
    assert not _common.analysis(
        [_common.node("a"), _common.node("b")],
        [{"source": "a", "target": "b", "conditions": []}],
    ).graph_has_conditional_links()


def test_topological_sort():
    analysis = _common.analysis(
        [_common.node(n) for n in "abcd"],
        [
            {"source": "a", "target": "b"},
            {"source": "a", "target": "c"},
            {"source": "b", "target": "d"},
            {"source": "c", "target": "d"},
        ],
    )
    order = list(analysis.topological_sort())

    assert set(order) == {"a", "b", "c", "d"}
    assert order.index("a") < order.index("b") < order.index("d")
    assert order.index("a") < order.index("c") < order.index("d")


def test_topological_sort_of_cyclic_graph():
    analysis = _common.analysis(
        [_common.node("a"), _common.node("b")],
        [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "a", "conditions": _common.TRUE},
        ],
    )
    with pytest.raises(RuntimeError, match="cyclic"):
        list(analysis.topological_sort())
