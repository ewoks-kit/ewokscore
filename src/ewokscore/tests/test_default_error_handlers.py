from ewokscore.graph import load_graph
from ewokscore.node import get_node_label


def subsubmodel1():
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
    return {"graph": {"id": "subsubmodel1"}, "nodes": nodes, "links": links}


def submodel1():
    nodes = [
        {
            "id": "a",
            "label": "task2",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {"id": "b", "task_type": "graph", "task_identifier": subsubmodel1()},
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
    return {"graph": {"id": "submodel1"}, "nodes": nodes, "links": links}


def model1():
    nodes = [
        {
            "id": "a",
            "label": "task1",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {"id": "b", "task_type": "graph", "task_identifier": submodel1()},
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
    return {"graph": {"id": "model1"}, "nodes": nodes, "links": links}


def test_default_error_handlers1():
    graph = load_graph(model1()).graph

    links = dict()
    for (source_id, target_id), link_attrs in graph.edges.items():
        source_label = get_node_label(source_id, graph.nodes[source_id])
        target_label = get_node_label(target_id, graph.nodes[target_id])
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


def submodel2():
    graph = {
        "id": "submodel2",
        "input_nodes": [{"id": "in", "node": "a"}],
        "output_nodes": [{"id": "out", "node": "c"}],
    }
    nodes = [
        {
            "id": "a",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {
            "id": "b",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {
            "id": "c",
            "task_type": "method",
            "task_identifier": "dummy",
        },
    ]
    links = [
        {"source": "a", "target": "b", "map_all_data": True},
        {"source": "b", "target": "c", "map_all_data": True},
    ]
    return {"graph": graph, "nodes": nodes, "links": links}


def model2():
    nodes = [
        {
            "id": "start",
            "task_type": "method",
            "task_identifier": "dummy",
        },
        {
            "id": "error_graph",
            "task_type": "graph",
            "task_identifier": submodel2(),
            "default_error_node": True,
        },
        {
            "id": "end",
            "task_type": "method",
            "task_identifier": "dummy",
        },
    ]
    links = [
        {"source": "start", "target": "end", "map_all_data": True},
    ]
    return {"graph": {"id": "model2"}, "nodes": nodes, "links": links}


def test_default_error_handlers2():
    graph = load_graph(model2()).graph

    links = dict()
    for (source_id, target_id), link_attrs in graph.edges.items():
        source_label = get_node_label(source_id, graph.nodes[source_id])
        target_label = get_node_label(target_id, graph.nodes[target_id])
        links[(source_label, target_label)] = link_attrs

    expected = {
        ("start", "end"): {"map_all_data": True},
        ("start", "error_graph:a"): {"map_all_data": True, "on_error": True},
        ("end", "error_graph:a"): {"map_all_data": True, "on_error": True},
        ("error_graph:a", "error_graph:b"): {"map_all_data": True},
        ("error_graph:b", "error_graph:c"): {"map_all_data": True},
    }

    assert expected == links
