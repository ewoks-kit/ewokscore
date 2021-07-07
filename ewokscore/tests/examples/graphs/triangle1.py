from . import graph


@graph
def triangle1():
    task = "ewokscore.tests.examples.tasks.condsumtask.CondSumTask"
    nodes = [
        {"id": "task1", "inputs": {"a": 1}, "class": task},
        {"id": "task2", "inputs": {"b": 1}, "class": task},
        {"id": "task3", "inputs": {"b": 1}, "class": task},
    ]
    links = [
        {
            "source": "task1",
            "target": "task2",
            "arguments": {"a": "result"},
            "conditions": {"too_small": True},
        },
        {
            "source": "task2",
            "target": "task3",
            "arguments": {"a": "result"},
            "conditions": {"too_small": True},
        },
        {
            "source": "task3",
            "target": "task1",
            "arguments": {"a": "result"},
            "conditions": {"too_small": True},
        },
    ]

    expected = {"result": 10, "too_small": False}

    graph = {
        "links": links,
        "nodes": nodes,
    }

    return graph, expected
