from . import _common


def test_neighbours():
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "b", "c", "d")],
        [
            {"source": "a", "target": "c"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
        ],
    )

    assert set(analysis.node_successors("c")) == {"d"}
    assert set(analysis.node_predecessors("c")) == {"a", "b"}
    assert set(analysis.node_successors("d")) == set()
    assert set(analysis.node_predecessors("a")) == set()

    assert analysis.node_has_successors("c")
    assert not analysis.node_has_successors("d")
    assert analysis.node_has_predecessors("c")
    assert not analysis.node_has_predecessors("a")


def test_descendants_and_ancestors():
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "b", "c", "d")],
        [
            {"source": "a", "target": "b"},
            {"source": "a", "target": "c"},
            {"source": "b", "target": "d"},
            {"source": "c", "target": "d"},
        ],
    )

    assert analysis.descendants("a") == {"b", "c", "d"}
    assert analysis.descendants("b") == {"d"}
    assert analysis.descendants("d") == set()

    assert analysis.ancestors("d") == {"a", "b", "c"}
    assert analysis.ancestors("b") == {"a"}
    assert analysis.ancestors("a") == set()

    assert analysis.node_has_descendants("a")
    assert not analysis.node_has_descendants("d")
    assert analysis.node_has_ancestors("d")
    assert not analysis.node_has_ancestors("a")


def test_descendants_and_ancestors_in_cycle():
    """A node in a cycle is its own descendant and ancestor."""
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "b", "c")],
        [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "b", "conditions": _common.TRUE},
        ],
    )

    assert analysis.descendants("a") == {"b", "c"}
    assert analysis.descendants("b") == {"b", "c"}
    assert analysis.ancestors("b") == {"a", "b", "c"}
    assert analysis.ancestors("a") == set()
