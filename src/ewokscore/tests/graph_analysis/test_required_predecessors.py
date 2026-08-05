from . import _common


def test_required_predecessors():
    analysis = _common.analysis(
        [_common.node(n) for n in ("req", "cond", "opt", "target", "orphan")],
        [
            {"source": "req", "target": "target"},
            {"source": "cond", "target": "target", "conditions": _common.TRUE},
            {"source": "opt", "target": "target", "required": False},
        ],
    )

    assert set(analysis.required_predecessors("target")) == {"req"}
    assert analysis.has_required_predecessors("target")
    assert not analysis.has_required_predecessors("req")
    assert not analysis.has_required_predecessors("orphan")
