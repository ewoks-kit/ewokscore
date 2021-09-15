from . import graph


@graph
def triangle1():
    task = "ewokscore.tests.examples.tasks.condsumtask.CondSumTask"
    nodes = [
        {
            "id": "task1",
            "default_inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task2",
            "default_inputs": [{"name": "b", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task3",
            "default_inputs": [{"name": "b", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
    ]
    links = [
        {
            "source": "task1",
            "target": "task2",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
            "conditions": [{"source_output": "too_small", "value": True}],
        },
        {
            "source": "task2",
            "target": "task3",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
            "conditions": [{"source_output": "too_small", "value": True}],
        },
        {
            "source": "task3",
            "target": "task1",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
            "conditions": [{"source_output": "too_small", "value": True}],
        },
    ]

    expected = {"result": 10, "too_small": False}

    graph = {
        "links": links,
        "nodes": nodes,
    }

    return graph, expected
