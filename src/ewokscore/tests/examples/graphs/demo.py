from . import graph


@graph
def demo():
    sumtask = "ewokscore.tests.examples.tasks.sumtask.SumTask"
    sumlist = "ewokscore.tests.examples.tasks.sumlist.SumList"
    nodes = [
        {
            "id": "task0",
            "default_inputs": [
                {"name": "list", "value": [0, 1, 2]},
                {"name": "delay", "value": 0},
            ],
            "task_type": "class",
            "task_identifier": sumlist,
        },
        {
            "id": "task1",
            "default_inputs": [
                {"name": "a", "value": 1},
                {"name": "delay", "value": 0},
            ],
            "task_type": "class",
            "task_identifier": sumtask,
        },
        {
            "id": "task2",
            "default_inputs": [
                {"name": "a", "value": 2},
                {"name": "delay", "value": 0},
            ],
            "task_type": "class",
            "task_identifier": sumtask,
        },
        {
            "id": "task3",
            "default_inputs": [
                {"name": "b", "value": 3},
                {"name": "delay", "value": 0},
            ],
            "task_type": "class",
            "task_identifier": sumtask,
        },
        {
            "id": "task4",
            "default_inputs": [
                {"name": "b", "value": 4},
                {"name": "delay", "value": 0},
            ],
            "task_type": "class",
            "task_identifier": sumtask,
        },
        {
            "id": "task5",
            "default_inputs": [
                {"name": "b", "value": 5},
                {"name": "delay", "value": 0},
            ],
            "task_type": "class",
            "task_identifier": sumtask,
        },
        {
            "id": "task6",
            "default_inputs": [
                {"name": "b", "value": 6},
                {"name": "delay", "value": 0},
            ],
            "task_type": "class",
            "task_identifier": sumtask,
        },
    ]

    links = [
        {
            "source": "task0",
            "target": "task1",
            "data_mapping": [{"target_input": "a", "source_output": "sum"}],
        },
        {
            "source": "task1",
            "target": "task3",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task2",
            "target": "task4",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task3",
            "target": "task5",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task4",
            "target": "task5",
            "data_mapping": [{"target_input": "b", "source_output": "result"}],
        },
        {
            "source": "task5",
            "target": "task6",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
    ]

    graph = {
        "links": links,
        "nodes": nodes,
    }

    expected_results = {
        "task0": {"sum": 3},
        "task1": {"result": 3},
        "task2": {"result": 2},
        "task3": {"result": 6},
        "task4": {"result": 6},
        "task5": {"result": 12},
        "task6": {"result": 18},
    }

    return graph, expected_results
