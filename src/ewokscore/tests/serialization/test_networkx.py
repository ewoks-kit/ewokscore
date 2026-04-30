import json

import networkx as nx
import yaml

from ...graph import serialize
from . import example_data


def test_yaml_graph_serialization(tmp_path):
    G = nx.DiGraph()
    original_data = example_data.generate_example_data()
    G.add_node("node1", default_args=original_data)

    dest = tmp_path / "workflow.yaml"
    serialize.dump(G, destination=dest, representation="yaml")

    python_data = serialize.load(dest).nodes["node1"]["default_args"]
    example_data.assert_python_data(python_data, original_data)

    raw_data = yaml.safe_load(dest.read_text(encoding="utf-8"))
    raw_data = raw_data["nodes"][0]["default_args"]
    example_data.assert_raw_data(raw_data, original_data)


def test_json_graph_serialization(tmp_path):
    G = nx.DiGraph()
    original_data = example_data.generate_example_data()
    G.add_node("node1", default_args=original_data)

    dest = tmp_path / "workflow.json"
    serialize.dump(G, destination=dest, representation="json")

    python_data = serialize.load(dest).nodes["node1"]["default_args"]
    example_data.assert_python_data(python_data, original_data)

    raw_data = json.loads(dest.read_text(encoding="utf-8"))
    raw_data = raw_data["nodes"][0]["default_args"]
    example_data.assert_raw_data(raw_data, original_data)
