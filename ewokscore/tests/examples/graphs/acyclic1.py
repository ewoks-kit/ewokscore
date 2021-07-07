from . import graph


@graph
def acyclic1():
    task = "ewokscore.tests.examples.tasks.sumtask.SumTask"
    nodes = [
        {"id": "task1", "inputs": {"a": 1}, "class": task},
        {"id": "task2", "inputs": {"a": 2}, "class": task},
        {"id": "task3", "inputs": {"b": 3}, "class": task},
        {"id": "task4", "inputs": {"b": 4}, "class": task},
        {"id": "task5", "inputs": {"b": 5}, "class": task},
        {"id": "task6", "inputs": {"b": 6}, "class": task},
    ]

    links = [
        {"source": "task1", "target": "task3", "arguments": {"a": "result"}},
        {"source": "task2", "target": "task4", "arguments": {"a": "result"}},
        {"source": "task3", "target": "task5", "arguments": {"a": "result"}},
        {"source": "task4", "target": "task5", "arguments": {"b": "result"}},
        {"source": "task5", "target": "task6", "arguments": {"a": "result"}},
    ]

    graph = {
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "task1": {"result": 1},
        "task2": {"result": 2},
        "task3": {"result": 4},
        "task4": {"result": 6},
        "task5": {"result": 10},
        "task6": {"result": 16},
    }

    return graph, expected_results
