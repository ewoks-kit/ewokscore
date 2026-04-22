import networkx as nx
import numpy as np

from ewokscore.graph import serialize
from ewokscore.persistence.json import JsonProxy


def test_numpy_and_pickle_fallback(tmp_path):
    """Tests the Persistence layer (Output Caching)"""
    proxy = JsonProxy()

    # Test: NumPy Array & Scalars (JSON path)
    data_np = {
        "array": np.array([1, 2, 3]),
        "scalar": np.float64(10.5)
    }
    path_np = tmp_path / "np.json"
    proxy._dump(path_np, data_np)
    
    loaded_np = proxy._load(path_np)
    assert loaded_np["array"] == [1, 2, 3]
    assert loaded_np["scalar"] == 10.5
    
    # Test: Pickle Fallback (Objects JSON can't handle even with NumPy encoder)
    data_pickle = {"complex": 1 + 2j, "set": {1, 2, 3}}
    path_pickle = tmp_path / "fallback.json"
    
    proxy._dump(path_pickle, data_pickle)
    loaded_pickle = proxy._load(path_pickle)
    
    assert loaded_pickle["complex"] == 1 + 2j
    assert loaded_pickle["set"] == {1, 2, 3}

def test_yaml_serialization_with_numpy(tmp_path):
    """Tests Graph Serialization"""
    G = nx.DiGraph()
    G.add_node("node1", default_args={"data": np.array([1, 2, 3])})
    
    dest = tmp_path / "workflow.yaml"
    serialize.dump(G, destination=dest, representation="yaml")
    assert dest.exists()
    
    # load it back to be 100% sure
    G_loaded = serialize.load(dest)
    assert G_loaded.nodes["node1"]["default_args"]["data"] == [1, 2, 3]

def test_json_serialization_with_numpy(tmp_path):
    """Tests Graph Serialization (JSON Representation)"""
    G = nx.DiGraph()
    # Add a node with a numpy scalar and array
    G.add_node("node1", default_args={
        "threshold": np.float64(0.5),
        "mask": np.array([0, 1, 0])
    })
    
    dest = tmp_path / "workflow.json"
    # This specifically tests that 'cls=EwoksDataTypeJsonEncoder' is working in serialize.py
    serialize.dump(G, destination=dest, representation="json")
    
    assert dest.exists()
    G_loaded = serialize.load(dest)
    assert G_loaded.nodes["node1"]["default_args"]["threshold"] == 0.5
    assert G_loaded.nodes["node1"]["default_args"]["mask"] == [0, 1, 0]