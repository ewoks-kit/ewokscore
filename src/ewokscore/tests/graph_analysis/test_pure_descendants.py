from ...graph import load_graph
from . import _common


def test_node_pure_descendants_chain():
    """The whole chain depends on nothing but the root."""
    analysis = _common.analysis(
        [_common.node(f"n{i}") for i in range(4)],
        _common.chain("n0", "n1", "n2", "n3"),
    )

    assert list(analysis.node_pure_descendants("n0")) == ["n1", "n2", "n3"]
    assert list(analysis.node_pure_descendants("n0", include_node=True)) == [
        "n0",
        "n1",
        "n2",
        "n3",
    ]


def test_node_pure_descendants_stops_at_shared_dependency():
    analysis = _common.analysis(
        [_common.node(n) for n in ("root", "pure", "shared", "outside", "after")],
        [
            {"source": "root", "target": "pure"},
            {"source": "pure", "target": "shared"},
            {"source": "outside", "target": "shared"},
            {"source": "shared", "target": "after"},
        ],
    )

    # `shared` also depends on `outside`, so it and everything after it are impure
    assert set(analysis.node_pure_descendants("root")) == {"pure"}


def test_node_pure_descendants_diamond():
    """Both branches and the node merging them depend only on the root."""
    analysis = _common.analysis(
        [_common.node(n) for n in ("root", "left", "right", "merge")],
        [
            {"source": "root", "target": "left"},
            {"source": "root", "target": "right"},
            {"source": "left", "target": "merge"},
            {"source": "right", "target": "merge"},
        ],
    )

    assert set(analysis.node_pure_descendants("root")) == {"left", "right", "merge"}


def test_node_pure_descendants_cyclic_branch():
    """Nodes that only depend on each other and on the root are pure."""
    analysis = _common.analysis(
        [_common.node(n) for n in ("root", "a", "b")],
        [
            {"source": "root", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "a", "conditions": _common.TRUE},
        ],
    )

    assert set(analysis.node_pure_descendants("root")) == {"a", "b"}


def test_unused_default_error_handler_chain_is_removed():
    """An unused default error handler is removed together with everything that
    only depends on it, not just its direct successors.
    """
    taskgraph = load_graph(
        {
            "graph": {"id": "test", "schema_version": "1.2"},
            "nodes": [
                _common.node("a"),
                _common.node("handler", default_error_node=True),
                _common.node("h1"),
                _common.node("h2"),
            ],
            "links": [
                # `a` already has an error handler, so nothing needs the default one
                {"source": "a", "target": "a", "on_error": True},
                *_common.chain("handler", "h1", "h2"),
            ],
        }
    )

    assert set(taskgraph.graph.nodes) == {"a"}


def test_node_pure_descendants_without_descendants():
    analysis = _common.analysis(
        [_common.node("a"), _common.node("b")], _common.chain("a", "b")
    )

    assert list(analysis.node_pure_descendants("b")) == []
    assert list(analysis.node_pure_descendants("b", include_node=True)) == ["b"]
