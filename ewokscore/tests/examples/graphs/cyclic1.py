from . import graph


@graph
def cyclic1():
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
            "inputs": [{"name": "b", "value": 3}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task4",
            "inputs": [{"name": "b", "value": -1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task5",
            "inputs": [{"name": "b", "value": -1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task6",
            "inputs": [{"name": "b", "value": 0}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task7",
            "inputs": [{"name": "b", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
    ]

    links = [
        {
            "source": "task1",
            "target": "task2",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
        },
        {
            "source": "task2",
            "target": "task3",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
        },
        {
            "source": "task3",
            "target": "task4",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
        },
        {
            "source": "task4",
            "target": "task2",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
            "conditions": {"too_small": True},
        },
        {
            "source": "task4",
            "target": "task5",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
            "conditions": {"too_small": False},
        },
        {
            "source": "task5",
            "target": "task6",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
        },
        {
            "source": "task6",
            "target": "task2",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
            "conditions": {"too_small": True},
        },
        {
            "source": "task6",
            "target": "task7",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
            "conditions": {"too_small": False},
        },
    ]

    expected = {"result": 12, "too_small": False}

    graph = {
        "links": links,
        "nodes": nodes,
    }

    return graph, expected
