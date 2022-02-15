import pytest
import json
import yaml
from ewokscore.graph import load_graph


@pytest.mark.parametrize("with_ext", [True, False])
@pytest.mark.parametrize("representation", ["json", "yaml", None])
def test_graph_discovery(representation, with_ext, tmpdir):
    subgraph = {
        "graph": {"input_nodes": [{"id": "in", "node": "subnode1"}]},
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

    graph = {
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

    ext = ""
    if representation == "yaml":
        dump = yaml.dump
        if with_ext:
            ext = ".yml"
    elif representation == "json":
        dump = json.dump
        if with_ext:
            ext = ".json"
    else:
        dump = json.dump
        if with_ext:
            ext = ".json"

    destination = str(tmpdir / "subgraph" + ext)
    with open(destination, mode="w") as f:
        dump(subgraph, f)
    destination = str(tmpdir / "graph" + ext)
    with open(destination, mode="w") as f:
        dump(graph, f)

    ewoksgraph = load_graph(
        "graph", representation=representation, root_dir=str(tmpdir)
    )

    assert set(ewoksgraph.graph.nodes) == {"node1", ("node2", "subnode1")}
