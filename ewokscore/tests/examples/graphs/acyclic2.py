from . import graph


@graph
def acyclic2():
    task = "ewokscore.tests.examples.tasks.errorsumtask.ErrorSumTask"
    nodes = [
        {"id": "task1", "inputs": {"a": 1}, "class": task},
        {
            "id": "task2",
            "inputs": {"b": 2, "raise_error": True},
            "class": task,
        },
        {"id": "task3", "inputs": {"b": 3}, "class": task},
        {
            "id": "task4",
            "inputs": {"a": 3, "b": 4},
            "class": task,
        },
        {"id": "task5", "inputs": {"b": 5}, "class": task},
        {"id": "task6", "inputs": {"b": 6}, "class": task},
    ]

    links = [
        {"source": "task1", "target": "task2", "arguments": {"a": "result"}},
        {"source": "task2", "target": "task3", "arguments": {"a": "result"}},
        {
            "source": "task2",
            "target": "task4",
            "on_error": True,
        },
        {"source": "task3", "target": "task5", "arguments": {"a": "result"}},
        {"source": "task4", "target": "task6", "arguments": {"a": "result"}},
    ]

    graph = {
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "task1": {"result": 1},
        "task2": None,  # error
        "task3": None,  # error branch
        "task4": {"result": 7},
        "task5": None,  # error branch
        "task6": {"result": 13},
    }

    return graph, expected_results
