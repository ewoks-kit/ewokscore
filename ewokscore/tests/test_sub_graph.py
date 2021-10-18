from ewokscore import load_graph
from ewokscore.utils import qualname
from .utils import assert_taskgraph_result


def myfunc(name=None, value=0):
    print("name:", name, "value:", value)
    return value + 1


def test_sub_graph():
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
    tasks = ewoksgraph.execute()
    expected = {
        "node1": {"return_value": 1},
        ("node2", ("subnode1", "subsubnode1")): {"return_value": 2},
    }
    assert_taskgraph_result(ewoksgraph, expected, tasks=tasks)
