import pydantic
import pytest

from ewokscore import load_graph
from ewokscore.graph.schema.model import EwoksGraph
from ewokscore.tests.test_examples import get_graph
from ewokscore.tests.test_examples import graph_names


@pytest.mark.parametrize("graph_name", graph_names())
def test_correct_graphs(graph_name):
    graph, _ = get_graph(graph_name)
    graph_dict: dict = load_graph(graph).dump()

    # This should not raise any error
    EwoksGraph(**graph_dict)


def test_incorrect_graph():
    graph_dict = {
        "graph": {"id": "required"},
        "nodes": [
            {
                "id": "node2",
                "task_type": "klass",  # <-- Typo
                "task_identifier": "dummy",
            },
        ],
        "links": [],
    }
    with pytest.raises(
        pydantic.ValidationError,
        match="1 validation error for EwoksGraph\nnodes.0.task_type\n",
    ):
        EwoksGraph(**graph_dict)
