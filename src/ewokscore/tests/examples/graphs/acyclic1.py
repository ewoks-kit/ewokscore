from . import graph


@graph
def acyclic1():
    task = "ewokscore.tests.examples.tasks.sumtask.SumTask"
    nodes = [
        {
            "id": "task1",
            "default_inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
            "ows": {"position": "(323.0, 166.0)"},
        },
        {
            "id": "task2",
            "default_inputs": [{"name": "a", "value": 2}],
            "task_type": "class",
            "task_identifier": task,
            "ows": {"position": "(317.0, 320.0)"},
        },
        {
            "id": "task3",
            "default_inputs": [{"name": "b", "value": 3}],
            "task_type": "class",
            "task_identifier": task,
            "ows": {"position": "(575.0, 164.0)"},
        },
        {
            "id": "task4",
            "default_inputs": [{"name": "b", "value": 4}],
            "task_type": "class",
            "task_identifier": task,
            "ows": {"position": "(577.0, 321.0)"},
        },
        {
            "id": "task5",
            "default_inputs": [{"name": "b", "value": 5}],
            "task_type": "class",
            "task_identifier": task,
            "ows": {"position": "(808.0, 231.0)"},
        },
        {
            "id": "task6",
            "default_inputs": [{"name": "b", "value": 6}],
            "task_type": "class",
            "task_identifier": task,
            "ows": {"position": "(1042.0, 234.0)"},
        },
    ]

    links = [
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
        "task1": {"result": 1},
        "task2": {"result": 2},
        "task3": {"result": 4},
        "task4": {"result": 6},
        "task5": {"result": 10},
        "task6": {"result": 16},
    }

    return graph, expected_results
