import json
import yaml
import pytest
from ewokscore.graph import load_graph


@pytest.mark.parametrize("with_ext", [True, False])
@pytest.mark.parametrize("representation", ["json", "yaml", "json_module", None])
def test_graph_discovery(representation, with_ext, tmpdir):
    subgraph = {
        "graph": {"id": "subgraph", "input_nodes": [{"id": "in", "node": "subnode1"}]},
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
        "graph": {"id": "graph"},
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
    source = "graph"
    root_dir = None
    root_module = None
    if representation == "yaml":
        root_dir = str(tmpdir)
        dump = yaml.dump
        if with_ext:
            ext = ".yml"
    elif representation == "json":
        root_dir = str(tmpdir)
        dump = json.dump
        if with_ext:
            ext = ".json"
    elif representation == "json_module":
        root_module = "ewokscore.tests.examples.loadtest"
        if with_ext:
            source = root_module + "." + source
        else:
            representation = None
        dump = None
    else:
        root_dir = str(tmpdir)
        dump = json.dump
        if with_ext:
            ext = ".json"

    if dump is not None:
        destination = str(tmpdir / "subgraph" + ext)
        with open(destination, mode="w") as f:
            dump(subgraph, f)
        destination = str(tmpdir / "graph" + ext)
        with open(destination, mode="w") as f:
            dump(graph, f)

    ewoksgraph = load_graph(
        source,
        representation=representation,
        root_dir=root_dir,
        root_module=root_module,
    )

    assert set(ewoksgraph.graph.nodes) == {"node1", ("node2", "subnode1")}
