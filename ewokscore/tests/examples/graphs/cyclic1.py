from . import graph


@graph
def cyclic1():
    task = "ewokscore.tests.examples.tasks.condsumtask.CondSumTask"
    nodes = [
        {"id": "task1", "inputs": {"a": 1}, "class": task},
        {"id": "task2", "inputs": {"b": 1}, "class": task},
        {"id": "task3", "inputs": {"b": 3}, "class": task},
        {"id": "task4", "inputs": {"b": -1}, "class": task},
        {"id": "task5", "inputs": {"b": -1}, "class": task},
        {"id": "task6", "inputs": {"b": 0}, "class": task},
        {"id": "task7", "inputs": {"b": 1}, "class": task},
    ]

    links = [
        {"source": "task1", "target": "task2", "arguments": {"a": "result"}},
        {"source": "task2", "target": "task3", "arguments": {"a": "result"}},
        {"source": "task3", "target": "task4", "arguments": {"a": "result"}},
        {
            "source": "task4",
            "target": "task2",
            "arguments": {"a": "result"},
            "conditions": {"too_small": True},
        },
        {
            "source": "task4",
            "target": "task5",
            "arguments": {"a": "result"},
            "conditions": {"too_small": False},
        },
        {"source": "task5", "target": "task6", "arguments": {"a": "result"}},
        {
            "source": "task6",
            "target": "task2",
            "arguments": {"a": "result"},
            "conditions": {"too_small": True},
        },
        {
            "source": "task6",
            "target": "task7",
            "arguments": {"a": "result"},
            "conditions": {"too_small": False},
        },
    ]

    expected = {"result": 12, "too_small": False}

    graph = {
        "links": links,
        "nodes": nodes,
    }

    return graph, expected
