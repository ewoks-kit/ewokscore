from . import graph


@graph
def acyclic1():
    task = "ewokscore.tests.examples.tasks.sumtask.SumTask"
    nodes = [
        {
            "id": "task1",
            "inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task2",
            "inputs": [{"name": "a", "value": 2}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task3",
            "inputs": [{"name": "b", "value": 3}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task4",
            "inputs": [{"name": "b", "value": 4}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task5",
            "inputs": [{"name": "b", "value": 5}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task6",
            "inputs": [{"name": "b", "value": 6}],
            "task_type": "class",
            "task_identifier": task,
        },
    ]

    links = [
        {
            "source": "task1",
            "target": "task3",
            "arguments": [{"input": "a", "output": "result"}],
        },
        {
            "source": "task2",
            "target": "task4",
            "arguments": [{"input": "a", "output": "result"}],
        },
        {
            "source": "task3",
            "target": "task5",
            "arguments": [{"input": "a", "output": "result"}],
        },
        {
            "source": "task4",
            "target": "task5",
            "arguments": [{"input": "b", "output": "result"}],
        },
        {
            "source": "task5",
            "target": "task6",
            "arguments": [{"input": "a", "output": "result"}],
        },
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
