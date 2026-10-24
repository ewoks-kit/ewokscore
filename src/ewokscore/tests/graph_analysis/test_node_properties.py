from . import _common


def test_node_has_error_handlers():
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "b", "handler")],
        [
            {"source": "a", "target": "handler", "on_error": True},
            {"source": "a", "target": "b"},
        ],
    )

    assert analysis.node_has_error_handlers("a")
    assert not analysis.node_has_error_handlers("b")
    assert not analysis.node_has_error_handlers("handler")


def test_node_is_start_node():
    analysis = _common.analysis(
        [
            _common.node("a"),
            _common.node("b"),
            _common.node("forced", force_start_node=True),
        ],
        [{"source": "a", "target": "b"}, {"source": "b", "target": "forced"}],
    )

    assert analysis.node_is_start_node("a")
    assert not analysis.node_is_start_node("b")
    assert analysis.node_is_start_node("forced")


def test_node_is_pure_end_node():
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "b", "handler", "end")],
        [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "end"},
            {"source": "b", "target": "handler", "on_error": True},
        ],
    )

    assert not analysis.node_is_pure_end_node("a")
    # Only an error handler as successor besides `end`
    assert not analysis.node_is_pure_end_node("b")
    assert analysis.node_is_pure_end_node("end")
    assert analysis.node_is_pure_end_node("handler")


def test_node_is_pure_end_node_with_only_error_handlers():
    analysis = _common.analysis(
        [_common.node("a"), _common.node("handler")],
        [{"source": "a", "target": "handler", "on_error": True}],
    )

    assert analysis.node_is_pure_end_node("a")
    assert analysis.node_is_pure_end_node("handler")


def test_node_condition_values():
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "b", "c", "d")],
        [
            {"source": "a", "target": "b", "conditions": _common.TRUE},
            {"source": "a", "target": "c", "conditions": _common.FALSE},
            {
                "source": "a",
                "target": "d",
                "conditions": [{"source_output": "other", "value": 1}],
            },
        ],
    )

    assert analysis.node_condition_values("a") == {
        "result": {True, False},
        "other": {1},
    }
    assert analysis.node_condition_values("b") == {}


def test_node_condition_values_is_a_copy():
    analysis = _common.analysis(
        [_common.node("a"), _common.node("b")],
        [{"source": "a", "target": "b", "conditions": _common.TRUE}],
    )

    analysis.node_condition_values("a")["result"].add("injected")

    assert analysis.node_condition_values("a") == {"result": {True}}


def test_node_has_noncovered_conditions():
    covered = _common.analysis(
        [_common.node(n) for n in ("a", "b", "c")],
        [
            {"source": "a", "target": "b", "conditions": _common.TRUE},
            {"source": "a", "target": "c", "conditions": _common.FALSE},
        ],
    )
    assert not covered.node_has_noncovered_conditions("a")

    uncovered = _common.analysis(
        [_common.node("a"), _common.node("b")],
        [{"source": "a", "target": "b", "conditions": _common.TRUE}],
    )
    assert uncovered.node_has_noncovered_conditions("a")

    # A non-boolean value is only covered by an `else` link
    other = _common.analysis(
        [_common.node("a"), _common.node("b")],
        [
            {
                "source": "a",
                "target": "b",
                "conditions": [{"source_output": "result", "value": 10}],
            }
        ],
    )
    assert other.node_has_noncovered_conditions("a")

    with_else = _common.analysis(
        [
            _common.node("a", conditions_else_value="else"),
            _common.node("b"),
            _common.node("c"),
        ],
        [
            {
                "source": "a",
                "target": "b",
                "conditions": [{"source_output": "result", "value": 10}],
            },
            {
                "source": "a",
                "target": "c",
                "conditions": [{"source_output": "result", "value": "else"}],
            },
        ],
    )
    assert not with_else.node_has_noncovered_conditions("a")

    # `True` without a `False` or `else` link is not covered
    half_covered = _common.analysis(
        [_common.node("a", conditions_else_value="else"), _common.node("b")],
        [{"source": "a", "target": "b", "conditions": _common.TRUE}],
    )
    assert half_covered.node_has_noncovered_conditions("a")


def test_node_is_end_node():
    analysis = _common.analysis(
        [_common.node(n) for n in ("a", "b", "c")],
        [
            {"source": "a", "target": "b", "conditions": _common.TRUE},
            {"source": "b", "target": "c"},
        ],
    )

    # Not a pure end node, but its conditions are not covered
    assert analysis.node_is_end_node("a")
    assert not analysis.node_is_end_node("b")
    assert analysis.node_is_end_node("c")


def test_has_required_static_inputs():
    analysis = _common.analysis(
        [
            _common.class_node("covered", default_inputs=[{"name": "a", "value": 1}]),
            _common.class_node("uncovered"),
            _common.node("not_a_class"),
        ],
        [{"source": "covered", "target": "uncovered"}],
    )

    assert analysis.has_required_static_inputs("covered")
    assert not analysis.has_required_static_inputs("uncovered")
    # Non-class tasks never report required inputs
    assert not analysis.has_required_static_inputs("not_a_class")
