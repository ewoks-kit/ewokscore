from ewokscore.graph import load_graph
from ewokscore.node import get_node_label


def subsubmodel():
    nodes = [
        {
            "id": "a",
            "label": "task3",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {
            "id": "b",
            "label": "task4",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {
            "id": "c",
            "label": "special_task5",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {
            "id": "special_handler",
            "label": "special_handler3",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {
            "id": "graph_handler",
            "label": "graph_handler3",
            "task_type": "method",
            "task_identifier": "dummy",
            "default_error_node": True,
        },
    ]
    links = [
        {"source": "a", "target": "b", "map_all_data": True},
        {"source": "b", "target": "c", "map_all_data": True},
        {
            "source": "c",
            "target": "special_handler",
            "map_all_data": True,
            "on_error": True,
        },
    ]
    return {"nodes": nodes, "links": links}


def submodel():
    nodes = [
        {
            "id": "a",
            "label": "task2",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {"id": "b", "task_type": "graph", "task_identifier": subsubmodel()},
        {
            "id": "c",
            "label": "special_task6",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {
            "id": "special_handler",
            "label": "special_handler2",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {
            "id": "graph_handler",
            "label": "graph_handler2",
            "task_type": "method",
            "task_identifier": "dummy",
            "default_error_node": True,
        },
    ]
    links = [
        {"source": "a", "target": "b", "sub_target": "a", "map_all_data": True},
        {"source": "b", "target": "c", "sub_source": "c", "map_all_data": True},
        {
            "source": "c",
            "target": "special_handler",
            "map_all_data": True,
            "on_error": True,
        },
    ]
    return {"nodes": nodes, "links": links}


def model():
    nodes = [
        {
            "id": "a",
            "label": "task1",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {"id": "b", "task_type": "graph", "task_identifier": submodel()},
        {
            "id": "c",
            "label": "special_task7",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {
            "id": "special_handler",
            "label": "special_handler1",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {
            "id": "graph_handler",
            "label": "graph_handler1",
            "task_type": "method",
            "task_identifier": "dummy",
            "default_error_node": True,
        },
    ]
    links = [
        {"source": "a", "target": "b", "sub_target": "a", "map_all_data": True},
        {"source": "b", "target": "c", "sub_source": "c", "map_all_data": True},
        {
            "source": "c",
            "target": "special_handler",
            "map_all_data": True,
            "on_error": True,
        },
    ]
    return {"nodes": nodes, "links": links}


def test_default_error_handlers():
    graph = load_graph(model()).graph

    links = dict()
    for (source_id, target_id), link_attrs in graph.edges.items():
        source_label = get_node_label(graph.nodes[source_id], source_id)
        target_label = get_node_label(graph.nodes[target_id], target_id)
        links[(source_label, target_label)] = link_attrs

    expected = {
        # normal connection
        ("task1", "task2"): {"map_all_data": True},
        ("task2", "task3"): {"map_all_data": True},
        ("task3", "task4"): {"map_all_data": True},
        ("task4", "special_task5"): {"map_all_data": True},
        ("special_task5", "special_task6"): {"map_all_data": True},
        ("special_task6", "special_task7"): {"map_all_data": True},
        # error handlers of special tasks
        ("special_task5", "special_handler3"): {"map_all_data": True, "on_error": True},
        ("special_task6", "special_handler2"): {"map_all_data": True, "on_error": True},
        ("special_task7", "special_handler1"): {"map_all_data": True, "on_error": True},
        # error handlers of normal tasks
        ("task1", "graph_handler1"): {"map_all_data": True, "on_error": True},
        ("task2", "graph_handler2"): {"map_all_data": True, "on_error": True},
        ("task3", "graph_handler3"): {"map_all_data": True, "on_error": True},
        ("task4", "graph_handler3"): {"map_all_data": True, "on_error": True},
        # error handlers of special handlers
        ("special_handler1", "graph_handler1"): {
            "map_all_data": True,
            "on_error": True,
        },
        ("special_handler2", "graph_handler2"): {
            "map_all_data": True,
            "on_error": True,
        },
        ("special_handler3", "graph_handler3"): {
            "map_all_data": True,
            "on_error": True,
        },
        # error handlers of graph handlers
        ("graph_handler2", "graph_handler1"): {"map_all_data": True, "on_error": True},
        ("graph_handler3", "graph_handler2"): {"map_all_data": True, "on_error": True},
    }

    assert expected == links
