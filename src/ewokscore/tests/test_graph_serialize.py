import json
from pathlib import Path

import pytest
import yaml

from ..graph import load_graph


@pytest.mark.parametrize("with_ext", [True, False])
@pytest.mark.parametrize("with_representation", [True, False])
@pytest.mark.parametrize("path_format", [str, Path])
def test_graph_discovery_json(with_ext, with_representation, tmp_path, path_format):
    _dump_graph_and_subgraph(tmp_path, "json", with_ext)

    ewoksgraph = load_graph(
        source=path_format("graph"),
        representation="json" if with_representation else None,
        root_dir=path_format(tmp_path),
    )

    assert set(ewoksgraph.graph.nodes) == {"node1", ("node2", "subnode1")}


@pytest.mark.parametrize("with_ext", [True, False])
@pytest.mark.parametrize("with_representation", [True, False])
@pytest.mark.parametrize("path_format", [str, Path])
def test_graph_discovery_yaml(with_ext, with_representation, tmp_path, path_format):
    _dump_graph_and_subgraph(tmp_path, "yaml", with_ext)

    ewoksgraph = load_graph(
        source=path_format("graph"),
        representation="yaml" if with_representation else None,
        root_dir=path_format(tmp_path),
    )

    assert set(ewoksgraph.graph.nodes) == {"node1", ("node2", "subnode1")}


@pytest.mark.parametrize("with_representation", [True, False])
def test_graph_discovery_json_module(with_representation):
    if with_representation:
        source = "ewokscore.tests.examples.loadtest.graph"
        representation = "json_module"
    else:
        source = "graph"
        representation = None

    ewoksgraph = load_graph(
        source=source,
        representation=representation,
        root_module="ewokscore.tests.examples.loadtest",
    )

    assert set(ewoksgraph.graph.nodes) == {"node1", ("node2", "subnode1")}


def _dump_graph_and_subgraph(tmp_path, format, with_ext):
    if format == "yaml":
        dump = yaml.dump

    if format == "json":
        dump = json.dump

    ext = f".{format}" if with_ext else ""
    with open(tmp_path / f"subgraph{ext}", mode="w") as f:
        dump(_SUBGRAPH, f)
    with open(tmp_path / f"graph{ext}", mode="w") as f:
        dump(_GRAPH, f)


_SUBGRAPH = {
    "graph": {
        "id": "subgraph",
        "schema_version": "1.1",
        "input_nodes": [{"id": "in", "node": "subnode1"}],
    },
    "nodes": [
        {
            "id": "subnode1",
            "task_type": "method",
            "task_identifier": "dummy",
            "default_inputs": [
                {"name": "name", "value": "subnode1"},
                {"name": "value", "value": 0},
            ],
        }
    ],
}

_GRAPH = {
    "graph": {"id": "graph", "schema_version": "1.1"},
    "nodes": [
        {
            "id": "node1",
            "task_type": "method",
            "task_identifier": "dummy",
            "default_inputs": [
                {"name": "name", "value": "node1"},
                {"name": "value", "value": 0},
            ],
        },
        {"id": "node2", "task_type": "graph", "task_identifier": "subgraph"},
    ],
    "links": [
        {
            "source": "node1",
            "target": "node2",
            "sub_target": "in",
            "data_mapping": [
                {"target_input": "value", "source_output": "return_value"}
            ],
        }
    ],
}
