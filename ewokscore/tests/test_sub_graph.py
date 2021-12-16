from ewokscore import load_graph
from ewokscore.utils import qualname
from .utils import assert_execute_graph_all_tasks
from ewokscore.node import node_id_as_string


def myfunc(name=None, value=0):
    print("name:", name, "value:", value)
    return value + 1


def test_sub_graph_execute():
    subsubgraph = {
        "graph": {"input_nodes": [{"id": "in", "node": "subsubnode1"}]},
        "nodes": [
            {
                "id": "subsubnode1",
                "task_type": "method",
                "task_identifier": qualname(myfunc),
                "default_inputs": [
                    {"name": "name", "value": "subsubnode1"},
                    {"name": "value", "value": 0},
                ],
            }
        ],
    }

    subgraph = {
        "graph": {"input_nodes": [{"id": "in", "node": "subnode1", "sub_node": "in"}]},
        "nodes": [
            {"id": "subnode1", "task_type": "graph", "task_identifier": subsubgraph}
        ],
    }

    graph = {
        "nodes": [
            {
                "id": "node1",
                "task_type": "method",
                "task_identifier": qualname(myfunc),
                "default_inputs": [
                    {"name": "name", "value": "node1"},
                    {"name": "value", "value": 0},
                ],
            },
            {"id": "node2", "task_type": "graph", "task_identifier": subgraph},
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

    ewoksgraph = load_graph(graph)
    result = ewoksgraph.execute(results_of_all_nodes=True)
    expected = {
        "node1": {"return_value": 1},
        ("node2", ("subnode1", "subsubnode1")): {"return_value": 2},
    }
    assert_execute_graph_all_tasks(ewoksgraph, expected, execute_graph_result=result)


def test_sub_graph_link_attributes():
    subsubgraph = {
        "graph": {
            "input_nodes": [
                {"id": "in1", "node": "subsubnode1", "link_attributes": {1: 1}},
                {"id": "in2", "node": "subsubnode1", "link_attributes": {2: 2}},
            ],
            "output_nodes": [
                {"id": "out1", "node": "subsubnode1", "link_attributes": {3: 3}},
                {"id": "out2", "node": "subsubnode1", "link_attributes": {4: 4}},
            ],
        },
        "nodes": [
            {"id": "subsubnode1", "task_type": "method", "task_identifier": "dummy"}
        ],
    }

    subgraph = {
        "graph": {
            "input_nodes": [
                {
                    "id": "in1",
                    "node": "subnode1",
                    "sub_node": "in1",
                    "link_attributes": {5: 5},
                },
                {
                    "id": "in2",
                    "node": "subnode1",
                    "sub_node": "in2",
                },
            ],
            "output_nodes": [
                {
                    "id": "out1",
                    "node": "subnode1",
                    "sub_node": "out1",
                    "link_attributes": {6: 6},
                },
                {
                    "id": "out2",
                    "node": "subnode1",
                    "sub_node": "out2",
                },
            ],
        },
        "nodes": [
            {"id": "subnode1", "task_type": "graph", "task_identifier": subsubgraph}
        ],
    }

    graph = {
        "nodes": [
            {"id": "node1", "task_type": "method", "task_identifier": "dummy"},
            {"id": "node2", "task_type": "method", "task_identifier": "dummy"},
            {"id": "node3", "task_type": "method", "task_identifier": "dummy"},
            {"id": "node4", "task_type": "method", "task_identifier": "dummy"},
            {"id": "graphnode", "task_type": "graph", "task_identifier": subgraph},
        ],
        "links": [
            {"source": "node1", "target": "graphnode", "sub_target": "in1"},
            {"source": "node2", "target": "graphnode", "sub_target": "in2"},
            {"source": "graphnode", "target": "node3", "sub_source": "out1"},
            {"source": "graphnode", "target": "node4", "sub_source": "out2"},
        ],
    }

    ewoksgraph = load_graph(graph)
    for link, attrs in ewoksgraph.graph.edges.items():
        numbers = {i for i in attrs if isinstance(i, int)}
        if "node1" in link:
            assert numbers == {1, 5}
        elif "node2" in link:
            assert numbers == {2}
        elif "node3" in link:
            assert numbers == {3, 6}
        elif "node4" in link:
            assert numbers == {4}
        else:
            assert False, "unexpected link"


def test_sub_graph_duplicate_aliases():
    subsubgraph = {
        "graph": {
            "input_nodes": [
                {
                    "id": "in",
                    "node": "inode1",
                },
                {
                    "id": "in",
                    "node": "inode2",
                },
            ],
            "output_nodes": [
                {
                    "id": "out",
                    "node": "inode4",
                },
                {
                    "id": "out",
                    "node": "inode5",
                },
            ],
        },
        "nodes": [
            {"id": "inode1", "task_type": "method", "task_identifier": "dummy"},
            {"id": "inode2", "task_type": "method", "task_identifier": "dummy"},
            {"id": "inode3", "task_type": "method", "task_identifier": "dummy"},
            {"id": "inode4", "task_type": "method", "task_identifier": "dummy"},
            {"id": "inode5", "task_type": "method", "task_identifier": "dummy"},
        ],
        "links": [
            {"source": "inode1", "target": "inode3"},
            {"source": "inode2", "target": "inode3"},
            {"source": "inode3", "target": "inode4"},
            {"source": "inode3", "target": "inode5"},
        ],
    }

    subgraph = {
        "graph": {
            "input_nodes": [
                {
                    "id": "in",
                    "node": "nonode",
                    "sub_node": "in",
                },
            ],
            "output_nodes": [
                {
                    "id": "out",
                    "node": "nonode",
                    "sub_node": "out",
                },
            ],
        },
        "nodes": [
            {"id": "nonode", "task_type": "graph", "task_identifier": subsubgraph}
        ],
    }

    graph = {
        "nodes": [
            {"id": "node1", "task_type": "method", "task_identifier": "dummy"},
            {"id": "node2", "task_type": "method", "task_identifier": "dummy"},
            {"id": "graphnode", "task_type": "graph", "task_identifier": subgraph},
        ],
        "links": [
            {"source": "node1", "target": "graphnode", "sub_target": "in"},
            {"source": "graphnode", "target": "node2", "sub_source": "out"},
        ],
    }

    ewoksgraph = load_graph(graph)
    links = {
        (node_id_as_string(source), node_id_as_string(target))
        for source, target in ewoksgraph.graph.edges
    }
    expected = {
        ("graphnode:nonode:inode1", "graphnode:nonode:inode3"),
        ("graphnode:nonode:inode2", "graphnode:nonode:inode3"),
        ("graphnode:nonode:inode3", "graphnode:nonode:inode4"),
        ("graphnode:nonode:inode3", "graphnode:nonode:inode5"),
        ("graphnode:nonode:inode4", "node2"),
        ("graphnode:nonode:inode5", "node2"),
        ("node1", "graphnode:nonode:inode1"),
        ("node1", "graphnode:nonode:inode2"),
    }

    assert links == expected
