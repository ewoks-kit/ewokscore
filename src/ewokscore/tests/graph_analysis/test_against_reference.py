"""Complex and randomly generated graphs checked against reference
implementations built from `networkx` reachability and set algebra, which
share no logic with the implementation under test.
"""

import itertools
import random
from typing import Any
from typing import Dict
from typing import Iterator
from typing import Set

import networkx
import pytest

from ...graph import load_graph
from ...graph._analysis import GraphAnalysis
from ...node import NodeIdType
from . import _common


def test_link_is_required_against_reference(reference_graph):
    analysis = GraphAnalysis(reference_graph)

    for source_id, target_id in reference_graph.edges:
        assert analysis.link_is_required(
            source_id, target_id
        ) == _expected_link_is_required(reference_graph, source_id, target_id), (
            source_id,
            target_id,
        )


def test_descendants_and_ancestors_against_reference(reference_graph):
    analysis = GraphAnalysis(reference_graph)

    for node_id in reference_graph.nodes:
        assert analysis.descendants(node_id) == _expected_reachable(
            reference_graph, node_id, upstream=False
        ), node_id
        assert analysis.ancestors(node_id) == _expected_reachable(
            reference_graph, node_id, upstream=True
        ), node_id


def test_pure_descendants_against_reference(reference_graph):
    analysis = GraphAnalysis(reference_graph)

    for node_id in reference_graph.nodes:
        assert set(analysis.node_pure_descendants(node_id)) == (
            _expected_pure_descendants(reference_graph, node_id)
        ), node_id


def test_start_and_end_nodes_against_reference(reference_graph):
    analysis = GraphAnalysis(reference_graph)

    expected_start = {
        node_id
        for node_id, node_attrs in reference_graph.nodes.items()
        if node_attrs.get("force_start_node", False)
        or reference_graph.in_degree(node_id) == 0
    }
    if expected_start:
        assert analysis.start_nodes() == expected_start
    else:
        # Fall back to the nodes that can be executed right away
        assert all(
            not analysis.has_required_predecessors(node_id)
            for node_id in analysis.start_nodes()
        )

    expected_end = {
        node_id
        for node_id in reference_graph.nodes
        if all(
            attrs.get("on_error", False)
            for attrs in reference_graph.succ[node_id].values()
        )
    }
    if expected_end:
        assert analysis.end_nodes() == expected_end
    else:
        assert analysis.end_nodes() == {
            node_id
            for node_id in reference_graph.nodes
            if _expected_has_noncovered_conditions(reference_graph, node_id)
        }


def test_noncovered_conditions_against_reference(reference_graph):
    analysis = GraphAnalysis(reference_graph)

    for node_id in reference_graph.nodes:
        assert analysis.node_has_noncovered_conditions(
            node_id
        ) == _expected_has_noncovered_conditions(reference_graph, node_id), node_id


def test_node_and_link_properties_against_reference(reference_graph):
    """Single node and link properties read straight from the graph attributes."""
    analysis = GraphAnalysis(reference_graph)

    for source_id, target_id in reference_graph.edges:
        attrs = reference_graph.edges[source_id, target_id]
        assert analysis.link_has_conditions(source_id, target_id) == bool(
            attrs.get("conditions")
        )
        assert analysis.link_has_on_error(source_id, target_id) == bool(
            attrs.get("on_error")
        )
        assert analysis.link_is_conditional(source_id, target_id) == (
            bool(attrs.get("conditions")) or bool(attrs.get("on_error"))
        )
        assert analysis.link_is_explicitly_required(source_id, target_id) == (
            attrs.get("required") is True
        )
        assert analysis.link_is_explicitly_optional(source_id, target_id) == (
            attrs.get("required") is False
        )

    for node_id in reference_graph.nodes:
        assert analysis.node_has_error_handlers(node_id) == any(
            attrs.get("on_error", False)
            for attrs in reference_graph.succ[node_id].values()
        )
        assert set(analysis.node_successors(node_id)) == set(
            reference_graph.successors(node_id)
        )
        assert set(analysis.node_predecessors(node_id)) == set(
            reference_graph.predecessors(node_id)
        )
        assert set(analysis.required_predecessors(node_id)) == {
            source_id
            for source_id in reference_graph.predecessors(node_id)
            if _expected_link_is_required(reference_graph, source_id, node_id)
        }


def test_graph_properties_against_reference(reference_graph):
    analysis = GraphAnalysis(reference_graph)

    assert analysis.graph_is_cyclic() == (
        not networkx.is_directed_acyclic_graph(reference_graph)
    )
    assert analysis.graph_has_conditional_links() == any(
        attrs.get("conditions") or attrs.get("on_error")
        for attrs in reference_graph.edges.values()
    )

    if analysis.graph_is_cyclic():
        with pytest.raises(RuntimeError):
            list(analysis.topological_sort())
    else:
        order = list(analysis.topological_sort())
        assert set(order) == set(reference_graph.nodes)
        position = {node_id: index for index, node_id in enumerate(order)}
        for source_id, target_id in reference_graph.edges:
            assert position[source_id] < position[target_id]


def _link_is_locally_optional(link_attrs: dict) -> bool:
    """The specification: explicit `required` wins, conditional links are optional."""
    required = link_attrs.get("required", None)
    if required is not None and isinstance(required, bool):
        return not required
    return bool(link_attrs.get("conditions")) or bool(link_attrs.get("on_error"))


def _expected_link_is_required(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    """Reference implementation for `link_is_required` using `networkx.ancestors`.

    A link is required when it is not locally optional and no link coming into
    its source or into any ancestor of its source is locally optional.
    """
    link_attrs = graph.edges[source_id, target_id]
    required = link_attrs.get("required", None)
    if isinstance(required, bool):
        return required
    if _link_is_locally_optional(link_attrs):
        return False

    upstream = networkx.ancestors(graph, source_id) | {source_id}
    return not any(
        _link_is_locally_optional(attrs)
        for _, _, attrs in graph.in_edges(upstream, data=True)
    )


def _expected_has_noncovered_conditions(
    graph: networkx.DiGraph, node_id: NodeIdType
) -> bool:
    """Reference implementation for `node_has_noncovered_conditions`, restating the specification:
    every condition value needs a link covering its complement.
    """
    else_value = graph.nodes[node_id].get("conditions_else_value", None)

    values_per_output: Dict[str, Set[Any]] = dict()
    for _, _, attrs in graph.out_edges(node_id, data=True):
        for condition in attrs.get("conditions") or ():
            values_per_output.setdefault(condition["source_output"], set()).add(
                condition["value"]
            )

    for values in values_per_output.values():
        for value in values:
            if value is True:
                covered_by = {False, else_value}
            elif value is False:
                covered_by = {True, else_value}
            else:
                covered_by = {else_value}
            if not (covered_by & values):
                return True
    return False


def _expected_reachable(
    graph: networkx.DiGraph, node_id: NodeIdType, upstream: bool
) -> Set[NodeIdType]:
    """Reference implementation for `descendants`/`ancestors`: the union over the direct neighbours
    of themselves and everything reachable from them.
    """
    if upstream:
        neighbours = graph.predecessors(node_id)
        reachable = networkx.ancestors
    else:
        neighbours = graph.successors(node_id)
        reachable = networkx.descendants

    result: Set[NodeIdType] = set()
    for neighbour_id in neighbours:
        result.add(neighbour_id)
        result |= reachable(graph, neighbour_id)
    return result


def _expected_pure_descendants(
    graph: networkx.DiGraph, node_id: NodeIdType
) -> Set[NodeIdType]:
    """Reference implementation for `node_pure_descendants`.

    Remove `node_id` from the graph: a descendant is impure when it is still
    reachable from a node that is not a descendant of `node_id`.
    """
    candidates = networkx.descendants(graph, node_id) - {node_id}

    without_node = graph.copy()
    without_node.remove_node(node_id)

    impure = set(without_node) - candidates
    for outside_id in set(impure):
        impure |= networkx.descendants(without_node, outside_id)
    return candidates - impure


def _complex_graph() -> networkx.DiGraph:
    """Layered graph combining every feature the analysis reacts to."""
    nodes = [
        _common.node("entry"),
        _common.node("fan", conditions_else_value=False),
        _common.node("branch_true"),
        _common.node("branch_false"),
        _common.node("merge"),
        _common.node("tail"),
        _common.node("optional_source"),
        _common.node("explicit_target"),
        _common.node("looper"),
        _common.node("global_handler", default_error_node=True),
        _common.node("after_handler"),
        _common.class_node("static", default_inputs=[{"name": "a", "value": 1}]),
    ]
    links = [
        {"source": "entry", "target": "fan"},
        {"source": "fan", "target": "branch_true", "conditions": _common.TRUE},
        {"source": "fan", "target": "branch_false", "conditions": _common.FALSE},
        {"source": "branch_true", "target": "merge"},
        {"source": "branch_false", "target": "merge"},
        {"source": "merge", "target": "tail"},
        {"source": "optional_source", "target": "explicit_target", "required": False},
        {"source": "explicit_target", "target": "tail", "required": True},
        {"source": "tail", "target": "looper"},
        {"source": "looper", "target": "tail", "conditions": _common.TRUE},
        {"source": "global_handler", "target": "after_handler"},
        {"source": "static", "target": "merge"},
    ]
    return load_graph(
        {
            "graph": {"id": "complex", "schema_version": "1.2"},
            "nodes": nodes,
            "links": links,
        }
    ).graph


def _random_graph(seed: int) -> networkx.DiGraph:
    """Random graph using the full range of node and link attributes.

    Links closing a cycle are always conditional, since a cycle of unconditional
    links has no consistent `link_is_required` solution.
    """
    rng = random.Random(seed)  # noqa: S311
    num_nodes = rng.randint(2, 10)
    node_ids = [f"node{i}" for i in range(num_nodes)]

    nodes = []
    for node_id in node_ids:
        attrs: Dict[str, Any] = dict()
        if rng.random() < 0.2:
            attrs["force_start_node"] = True
        if rng.random() < 0.2:
            attrs["conditions_else_value"] = rng.choice([None, False, "else"])
        if rng.random() < 0.3:
            default_inputs = [{"name": "a", "value": 1}] if rng.random() < 0.5 else []
            nodes.append(
                _common.class_node(node_id, default_inputs=default_inputs, **attrs)
            )
        else:
            nodes.append(_common.node(node_id, **attrs))

    links = []
    for source, target in itertools.product(range(num_nodes), range(num_nodes)):
        if rng.random() > 0.3:
            continue
        link: Dict[str, Any] = {
            "source": node_ids[source],
            "target": node_ids[target],
        }
        kind = rng.random()
        if target <= source or kind < 0.25:
            link["conditions"] = [
                {"source_output": "result", "value": rng.choice([True, False, 10])}
            ]
        elif kind < 0.4:
            link["on_error"] = True
        if rng.random() < 0.3:
            link["required"] = rng.choice([True, False])
        links.append(link)

    if not links:
        links.append({"source": node_ids[0], "target": node_ids[-1]})

    return load_graph(
        {
            "graph": {"id": f"random{seed}", "schema_version": "1.2"},
            "nodes": nodes,
            "links": links,
        }
    ).graph


def _reference_graphs() -> Iterator[networkx.DiGraph]:
    yield _complex_graph()
    for seed in range(40):
        yield _random_graph(seed)


_REFERENCE_GRAPHS = {
    graph.graph.get("id", str(index)): graph
    for index, graph in enumerate(_reference_graphs())
}


@pytest.fixture(params=list(_REFERENCE_GRAPHS))
def reference_graph(request) -> networkx.DiGraph:
    return _REFERENCE_GRAPHS[request.param]
