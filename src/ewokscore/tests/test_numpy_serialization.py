import networkx as nx
import numpy as np

from ewokscore.graph import serialize
from ewokscore.persistence.json import JsonProxy


def test_numpy_and_pickle_fallback(tmp_path):
    proxy = JsonProxy()
    data_np = {"array": np.array([1, 2, 3]), "scalar": np.float64(10.5)}
    path_np = tmp_path / "np.json"
    proxy._dump(path_np, data_np)

    loaded_np = proxy._load(path_np)
    assert isinstance(loaded_np["array"], np.ndarray)
    np.testing.assert_array_equal(loaded_np["array"], data_np["array"])
    assert loaded_np["scalar"] == 10.5


def test_yaml_serialization_with_numpy(tmp_path):
    G = nx.DiGraph()
    original_arr = np.array([1, 2, 3])
    G.add_node("node1", default_args={"data": original_arr})

    dest = tmp_path / "workflow.yaml"
    serialize.dump(G, destination=dest, representation="yaml")

    G_loaded = serialize.load(dest)
    assert isinstance(G_loaded.nodes["node1"]["default_args"]["data"], np.ndarray)
    np.testing.assert_array_equal(
        G_loaded.nodes["node1"]["default_args"]["data"], original_arr
    )


def test_json_serialization_with_numpy(tmp_path):
    G = nx.DiGraph()
    original_arr = np.array([10, 20, 30], dtype=np.int32)
    G.add_node("task1", default_args={"values": original_arr})

    dest = tmp_path / "workflow.json"
    serialize.dump(G, destination=dest, representation="json")

    G_loaded = serialize.load(dest)
    loaded_data = G_loaded.nodes["task1"]["default_args"]["values"]
    assert isinstance(loaded_data, np.ndarray), (
        "Data should be reconstructed as np.ndarray"
    )
    np.testing.assert_array_equal(loaded_data, original_arr)
    assert loaded_data.dtype == np.int32
