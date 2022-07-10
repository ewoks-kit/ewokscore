from ewokscore.graph import load_graph
from ewokscore.graph.analysis import start_nodes
from ewokscore.graph.analysis import end_nodes


def test_graph_start_end_nodes():
    nodes = [
        {"id": "start1", "task_type": "method", "task_identifier": "dummy"},
        {"id": "start2", "task_type": "method", "task_identifier": "dummy"},
        {"id": "begin", "task_type": "method", "task_identifier": "dummy"},
        {"id": "fan", "task_type": "method", "task_identifier": "dummy"},
        {"id": "always1", "task_type": "method", "task_identifier": "dummy"},
        {"id": "on_true1", "task_type": "method", "task_identifier": "dummy"},
        {"id": "on_error1", "task_type": "method", "task_identifier": "dummy"},
        {"id": "always2", "task_type": "method", "task_identifier": "dummy"},
        {"id": "on_true2", "task_type": "method", "task_identifier": "dummy"},
        {"id": "on_error2", "task_type": "method", "task_identifier": "dummy"},
        {"id": "merge", "task_type": "method", "task_identifier": "dummy"},
        {"id": "end_always", "task_type": "method", "task_identifier": "dummy"},
        {"id": "end_on_error", "task_type": "method", "task_identifier": "dummy"},
    ]
    links = [
        {"source": "start1", "target": "begin", "map_all_data": True},
        {"source": "start2", "target": "begin", "map_all_data": True},
        {
            "source": "begin",
            "target": "start2",
            "map_all_data": True,
            "conditions": [{"source_output": "result", "value": True}],
        },
        {"source": "begin", "target": "fan", "map_all_data": True},
        {"source": "fan", "target": "always1", "map_all_data": True},
        {
            "source": "fan",
            "target": "on_true1",
            "map_all_data": True,
            "conditions": [{"source_output": "result", "value": True}],
        },
        {
            "source": "fan",
            "target": "on_error1",
            "map_all_data": True,
            "on_error": True,
        },
        {"source": "always1", "target": "always2", "map_all_data": True},
        {"source": "on_true1", "target": "on_true2", "map_all_data": True},
        {"source": "on_error1", "target": "on_error2", "map_all_data": True},
        {"source": "always2", "target": "merge", "map_all_data": True},
        {"source": "on_true2", "target": "merge", "map_all_data": True},
        {"source": "on_error2", "target": "merge", "map_all_data": True},
        {"source": "merge", "target": "end_always", "map_all_data": True},
        {"source": "on_error2", "target": "end_on_error", "map_all_data": True},
    ]
    taskgraph = load_graph({"graph": {"id": "test"}, "nodes": nodes, "links": links})

    assert start_nodes(taskgraph.graph) == {"start1"}
    assert end_nodes(taskgraph.graph) == {"end_always", "end_on_error"}
