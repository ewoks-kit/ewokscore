from copy import deepcopy

import pytest

from ..bindings import load_graph

_TASK = "ewokscore.tests.examples.tasks.sumtask.SumTask"


def _node(**kwargs):
    return {"id": "a", "task_type": "class", "task_identifier": _TASK, **kwargs}


@pytest.mark.parametrize(
    "graph,inputs",
    [
        ({"nodes": [_node()]}, None),
        (
            {
                "graph": {"id": "g"},
                "nodes": [_node(default_inputs=[{"name": "a", "value": 1}])],
            },
            [{"id": "a", "name": "a", "value": 10}],
        ),
        (
            {
                "graph": {"id": "g"},
                "nodes": [_node(default_inputs=[{"name": "a", "value": 1}])],
            },
            [{"id": "a", "name": "b", "value": 10}],
        ),
    ],
    ids=["missing_keys", "override_default_input", "add_default_input"],
)
def test_load_graph_does_not_modify_dict(graph, inputs):
    original = deepcopy(graph)
    load_graph(graph, inputs=inputs)
    assert graph == original


def test_load_graph_does_not_copy_input_values():
    value = object()
    graph = {
        "graph": {"id": "g"},
        "nodes": [_node(default_inputs=[{"name": "a", "value": value}])],
    }
    loaded = load_graph(graph)
    assert loaded.graph.nodes["a"]["default_inputs"][0]["value"] is value
