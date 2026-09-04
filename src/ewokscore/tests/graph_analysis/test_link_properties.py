from . import _common


def test_link_properties():
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "plain", "cond", "err", "req", "opt")],
        [
            {"source": "a", "target": "plain"},
            {"source": "a", "target": "cond", "conditions": _common.TRUE},
            {"source": "a", "target": "err", "on_error": True},
            {"source": "a", "target": "req", "required": True},
            {"source": "a", "target": "opt", "required": False},
        ],
    )

    assert not analysis.link_has_conditions("a", "plain")
    assert analysis.link_has_conditions("a", "cond")
    assert not analysis.link_has_conditions("a", "err")

    assert not analysis.link_has_on_error("a", "plain")
    assert analysis.link_has_on_error("a", "err")

    assert not analysis.link_is_conditional("a", "plain")
    assert analysis.link_is_conditional("a", "cond")
    assert analysis.link_is_conditional("a", "err")

    assert not analysis.link_is_explicitly_required("a", "plain")
    assert analysis.link_is_explicitly_required("a", "req")
    assert not analysis.link_is_explicitly_required("a", "opt")

    assert not analysis.link_is_explicitly_optional("a", "plain")
    assert not analysis.link_is_explicitly_optional("a", "req")
    assert analysis.link_is_explicitly_optional("a", "opt")


def test_link_is_required_unconditional_chain():
    """Everything is required when no link is conditional or explicit."""
    analysis = _common.analysis(
        [_common.node(f"n{i}") for i in range(4)],
        _common.chain("n0", "n1", "n2", "n3"),
    )

    assert analysis.link_is_required("n0", "n1")
    assert analysis.link_is_required("n1", "n2")
    assert analysis.link_is_required("n2", "n3")


def test_link_is_required_is_inherited_downstream():
    """A conditional link makes every link downstream of it optional."""
    analysis = _common.analysis(
        [_common.node(n) for n in ("start", "fan", "branch", "after", "last")],
        [
            {"source": "start", "target": "fan"},
            {"source": "fan", "target": "branch", "conditions": _common.TRUE},
            *_common.chain("branch", "after", "last"),
        ],
    )

    assert analysis.link_is_required("start", "fan")
    assert not analysis.link_is_required("fan", "branch")
    # Everything after the conditional link is optional
    assert not analysis.link_is_required("branch", "after")
    assert not analysis.link_is_required("after", "last")


def test_link_is_required_on_error_is_inherited_downstream():
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "handler", "after")],
        [
            {"source": "a", "target": "handler", "on_error": True},
            {"source": "handler", "target": "after"},
        ],
    )

    assert not analysis.link_is_required("a", "handler")
    assert not analysis.link_is_required("handler", "after")


def test_link_is_required_explicit_wins():
    """`required` overrules the analysis, but only for the link itself."""
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "b", "c", "d", "e")],
        [
            {
                "source": "a",
                "target": "b",
                "conditions": _common.TRUE,
                "required": True,
            },
            {"source": "b", "target": "c", "required": False},
            {"source": "c", "target": "d", "required": True},
            {"source": "d", "target": "e"},
        ],
    )

    # Explicitly required even though it is conditional
    assert analysis.link_is_required("a", "b")
    assert not analysis.link_is_required("b", "c")
    # Explicitly required even though something upstream is optional
    assert analysis.link_is_required("c", "d")
    # Not explicit, and something upstream is optional
    assert not analysis.link_is_required("d", "e")


def test_link_is_required_merging_branches():
    """One optional branch makes the merge and everything after it optional."""
    analysis = _common.analysis(
        [_common.node(n) for n in ("start", "always", "maybe", "merge", "end")],
        [
            {"source": "start", "target": "always"},
            {"source": "start", "target": "maybe", "conditions": _common.TRUE},
            {"source": "always", "target": "merge"},
            {"source": "maybe", "target": "merge"},
            {"source": "merge", "target": "end"},
        ],
    )

    assert analysis.link_is_required("start", "always")
    assert not analysis.link_is_required("start", "maybe")
    # `always` has nothing optional upstream of it
    assert analysis.link_is_required("always", "merge")
    assert not analysis.link_is_required("maybe", "merge")
    # `merge` has an optional link upstream of it
    assert not analysis.link_is_required("merge", "end")


def test_link_is_required_in_cyclic_graph():
    """A cycle broken by a conditional link is resolved without recursing."""
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "b", "c")],
        [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "a", "conditions": _common.TRUE},
        ],
    )

    # The conditional loopback into `a` makes everything after it optional
    assert not analysis.link_is_required("a", "b")
    assert not analysis.link_is_required("b", "c")
    assert not analysis.link_is_required("c", "a")
