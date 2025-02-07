from . import graph


@graph
def self_trigger():
    graph = {"id": "self_trigger", "label": "self_trigger", "schema_version": "1.1"}

    task = "ewokscore.tests.examples.tasks.condsumtask.CondSumTask"
    nodes = [
        {
            "id": "task1",
            "default_inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
            "force_start_node": True,
        },
        {
            "id": "task2",
            "default_inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task3",
            "task_type": "class",
            "task_identifier": task,
        },
    ]
    links = [
        {
            "source": "task1",
            "target": "task1",
            "data_mapping": [{"source_output": "result", "target_input": "b"}],
            "conditions": [{"source_output": "too_small", "value": True}],
        },
        {
            "source": "task1",
            "target": "task3",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task2",
            "target": "task3",
            "data_mapping": [{"source_output": "result", "target_input": "b"}],
        },
    ]

    expected = {
        "task3": {"too_small": False, "result": 11},
    }

    taskgraph = {"graph": graph, "links": links, "nodes": nodes}

    return taskgraph, expected
