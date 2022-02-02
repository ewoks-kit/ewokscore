from ewokscore.graph import load_graph


def test_graph_link_is_required_conditions1():
    nodes = [
        {"id": "start", "task_type": "method", "task_identifier": "dummy"},
        {"id": "fan", "task_type": "method", "task_identifier": "dummy"},
        {"id": "on_false1", "task_type": "method", "task_identifier": "dummy"},
        {"id": "on_true1", "task_type": "method", "task_identifier": "dummy"},
        {"id": "on_false2", "task_type": "method", "task_identifier": "dummy"},
        {"id": "on_true2", "task_type": "method", "task_identifier": "dummy"},
        {"id": "merge", "task_type": "method", "task_identifier": "dummy"},
        {"id": "end", "task_type": "method", "task_identifier": "dummy"},
    ]
    links = [
        {"source": "start", "target": "fan", "map_all_data": True},
        {
            "source": "fan",
            "target": "on_false1",
            "map_all_data": True,
            "conditions": [{"source_output": "result", "value": False}],
        },
        {
            "source": "fan",
            "target": "on_true1",
            "map_all_data": True,
            "conditions": [{"source_output": "result", "value": True}],
        },
        {"source": "on_false1", "target": "on_false2", "map_all_data": True},
        {"source": "on_true1", "target": "on_true2", "map_all_data": True},
        {"source": "on_false2", "target": "merge", "map_all_data": True},
        {"source": "on_true2", "target": "merge", "map_all_data": True},
        {"source": "merge", "target": "end", "map_all_data": True},
    ]
    taskgraph = load_graph({"nodes": nodes, "links": links})

    assert taskgraph.link_is_required("start", "fan")
    assert not taskgraph.link_is_required("fan", "on_false1")
    assert not taskgraph.link_is_required("fan", "on_true1")
    assert not taskgraph.link_is_required("on_false1", "on_false2")
    assert not taskgraph.link_is_required("on_true1", "on_true2")
    assert not taskgraph.link_is_required("on_false2", "merge")
    assert not taskgraph.link_is_required("on_true2", "merge")
    assert not taskgraph.link_is_required(
        "merge", "end"
    )  # TODO: this should be True because branches merge again


def test_graph_link_is_required_conditions2():
    nodes = [
        {"id": "start", "task_type": "method", "task_identifier": "dummy"},
        {"id": "fan", "task_type": "method", "task_identifier": "dummy"},
        {"id": "always1", "task_type": "method", "task_identifier": "dummy"},
        {"id": "on_true1", "task_type": "method", "task_identifier": "dummy"},
        {"id": "always2", "task_type": "method", "task_identifier": "dummy"},
        {"id": "on_true2", "task_type": "method", "task_identifier": "dummy"},
        {"id": "merge", "task_type": "method", "task_identifier": "dummy"},
        {"id": "end_always", "task_type": "method", "task_identifier": "dummy"},
    ]
    links = [
        {"source": "start", "target": "fan", "map_all_data": True},
        {"source": "fan", "target": "always1", "map_all_data": True},
        {
            "source": "fan",
            "target": "on_true1",
            "map_all_data": True,
            "conditions": [{"source_output": "result", "value": True}],
        },
        {"source": "always1", "target": "always2", "map_all_data": True},
        {"source": "on_true1", "target": "on_true2", "map_all_data": True},
        {"source": "always2", "target": "merge", "map_all_data": True},
        {"source": "on_true2", "target": "merge", "map_all_data": True},
        {"source": "merge", "target": "end_always", "map_all_data": True},
    ]
    taskgraph = load_graph({"nodes": nodes, "links": links})

    assert taskgraph.link_is_required("start", "fan")
    assert taskgraph.link_is_required("fan", "always1")
    assert not taskgraph.link_is_required("fan", "on_true1")
    assert taskgraph.link_is_required("always1", "always2")
    assert not taskgraph.link_is_required("on_true1", "on_true2")
    assert taskgraph.link_is_required("always2", "merge")
    assert not taskgraph.link_is_required("on_true2", "merge")
    assert not taskgraph.link_is_required(
        "merge", "end_always"
    )  # TODO: this should be True because branches merge again


def test_graph_link_is_required_errors():
    nodes = [
        {"id": "start", "task_type": "method", "task_identifier": "dummy"},
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
        {"source": "start", "target": "fan", "map_all_data": True},
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
    taskgraph = load_graph({"nodes": nodes, "links": links})

    assert taskgraph.link_is_required("start", "fan")
    assert taskgraph.link_is_required("fan", "always1")
    assert not taskgraph.link_is_required("fan", "on_true1")
    assert not taskgraph.link_is_required("fan", "on_error1")
    assert not taskgraph.link_is_required("always1", "always2")
    assert not taskgraph.link_is_required("on_true1", "on_true2")
    assert not taskgraph.link_is_required("on_error1", "on_error2")
    assert not taskgraph.link_is_required("always2", "merge")
    assert not taskgraph.link_is_required("on_true2", "merge")
    assert not taskgraph.link_is_required("on_error2", "merge")
    assert not taskgraph.link_is_required(
        "merge", "end_always"
    )  # TODO: this should be True because branches merge again
    assert not taskgraph.link_is_required("on_error2", "end_on_error")
