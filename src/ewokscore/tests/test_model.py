import pydantic
import pytest
from jsonschema.exceptions import SchemaError

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
        match="1 validation error for EwoksGraph\nnodes.0\n",
    ):
        EwoksGraph(**graph_dict)


def test_class_node_without_identifier():
    graph_dict = {
        "graph": {"id": "required"},
        "nodes": [
            {
                "id": "node2",
                "task_type": "class",
                # Missing task_identifier
            },
        ],
        "links": [],
    }
    with pytest.raises(
        pydantic.ValidationError,
        match="1 validation error for EwoksGraph\nnodes.0.class.task_identifier\n",
    ):
        EwoksGraph(**graph_dict)


def test_ppfport_node_without_identifier():
    graph_dict = {
        "graph": {"id": "required"},
        "nodes": [
            {
                "id": "node2",
                "task_type": "ppfport",
                # Missing task_identifier
            },
        ],
        "links": [],
    }

    # This should not raise any error
    EwoksGraph(**graph_dict)


def test_generated_node_without_generator():
    graph_dict = {
        "graph": {"id": "required"},
        "nodes": [
            {
                "id": "node2",
                "task_type": "generated",
                "task_identifier": "generator.arg",
                # Missing task_generator
            },
        ],
        "links": [],
    }

    with pytest.raises(
        pydantic.ValidationError,
        match="1 validation error for EwoksGraph\nnodes.0.generated.task_generator\n",
    ):
        EwoksGraph(**graph_dict)


def test_link_with_datamapping_and_map_all_data():
    graph_dict = {
        "graph": {"id": "required"},
        "nodes": [
            {
                "id": "node1",
                "task_type": "class",
                "task_identifier": "task1",
            },
            {
                "id": "node2",
                "task_type": "class",
                "task_identifier": "task2",
            },
        ],
        "links": [
            {
                "source": "task1",
                "target": "task2",
                "data_mapping": [
                    {
                        "source_output": "a",
                        "target_input": "b",
                    }
                ],
                "map_all_data": True,
            }
        ],
    }

    with pytest.raises(
        pydantic.ValidationError,
        match="1 validation error for EwoksGraph\nlinks.0\n",
    ):
        EwoksGraph(**graph_dict)


def test_wrong_type_in_schema():
    graph_dict = {
        "graph": {
            "id": "required",
            "workflow_input_schema": {"properties": {"a": {"type": "oo"}}},
        },
        "nodes": [
            {
                "id": "node1",
                "task_type": "class",
                "task_identifier": "task1",
            },
        ],
        "links": [],
    }
    with pytest.raises(SchemaError):
        EwoksGraph(**graph_dict)


def test_missing_name_in_ewoks_target():
    graph_dict = {
        "graph": {
            "id": "required",
            "workflow_input_schema": {
                "properties": {"a": {"type": "number", "x_ewoks_targets": [{}]}}
            },
        },
        "nodes": [
            {
                "id": "node1",
                "task_type": "class",
                "task_identifier": "task1",
            },
        ],
        "links": [],
    }

    with pytest.raises(
        pydantic.ValidationError,
        match="1 validation error for EwoksGraph\ngraph.workflow_input_schema.properties.a.x_ewoks_targets.0.name\n",
    ):
        EwoksGraph(**graph_dict)


def test_wrong_required_inputs():
    graph_dict = {
        "graph": {
            "id": "required",
            "workflow_input_schema": {
                "properties": {"a": {"type": "number"}},
                "required": ["not_a"],
            },
        },
        "nodes": [],
        "links": [],
    }

    with pytest.raises(
        pydantic.ValidationError,
        match="1 validation error for EwoksGraph\ngraph.workflow_input_schema\n",
    ):
        EwoksGraph(**graph_dict)
