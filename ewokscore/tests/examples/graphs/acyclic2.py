from . import graph


@graph
def acyclic2():
    task = "ewokscore.tests.examples.tasks.errorsumtask.ErrorSumTask"
    nodes = [
        {
            "id": "task1",
            "default_inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task2",
            "default_inputs": [
                {"name": "b", "value": 2},
                {"name": "raise_error", "value": True},
            ],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task3",
            "default_inputs": [{"name": "b", "value": 3}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task4",
            "default_inputs": [{"name": "a", "value": 3}, {"name": "b", "value": 4}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task5",
            "default_inputs": [{"name": "b", "value": 5}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task6",
            "default_inputs": [{"name": "b", "value": 6}],
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
            "source": "task2",
            "target": "task4",
            "on_error": True,
        },
        {
            "source": "task3",
            "target": "task5",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
        },
        {
            "source": "task4",
            "target": "task6",
            "data_mapping": [{"target_input": "a", "source_output": "result"}],
        },
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
