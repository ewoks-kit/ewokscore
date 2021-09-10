from . import graph


@graph
def triangle1():
    task = "ewokscore.tests.examples.tasks.condsumtask.CondSumTask"
    nodes = [
        {
            "id": "task1",
            "inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task2",
            "inputs": [{"name": "b", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task3",
            "inputs": [{"name": "b", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
    ]
    links = [
        {
            "source": "task1",
            "target": "task2",
            "arguments": [{"input": "a", "output": "result"}],
            "conditions": {"too_small": True},
        },
        {
            "source": "task2",
            "target": "task3",
            "arguments": [{"input": "a", "output": "result"}],
            "conditions": {"too_small": True},
        },
        {
            "source": "task3",
            "target": "task1",
            "arguments": [{"input": "a", "output": "result"}],
            "conditions": {"too_small": True},
        },
    ]

    expected = {"result": 10, "too_small": False}

    graph = {
        "links": links,
        "nodes": nodes,
    }

    return graph, expected
