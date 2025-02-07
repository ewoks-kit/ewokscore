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
            "uiProps": {"position": {"x": 323, "y": 166}},
        },
        {
            "id": "task2",
            "default_inputs": [{"name": "a", "value": 2}],
            "task_type": "class",
            "task_identifier": task,
            "ows": {"position": "(317.0, 320.0)"},
            "uiProps": {"position": {"x": 317, "y": 320}},
        },
        {
            "id": "task3",
            "default_inputs": [{"name": "b", "value": 3}],
            "task_type": "class",
            "task_identifier": task,
            "ows": {"position": "(575.0, 164.0)"},
            "uiProps": {"position": {"x": 575, "y": 164}},
        },
        {
            "id": "task4",
            "default_inputs": [{"name": "b", "value": 4}],
            "task_type": "class",
            "task_identifier": task,
            "ows": {"position": "(577.0, 321.0)"},
            "uiProps": {"position": {"x": 577, "y": 321}},
        },
        {
            "id": "task5",
            "default_inputs": [{"name": "b", "value": 5}],
            "task_type": "class",
            "task_identifier": task,
            "ows": {"position": "(808.0, 231.0)"},
            "uiProps": {"position": {"x": 808, "y": 231}},
        },
        {
            "id": "task6",
            "default_inputs": [{"name": "b", "value": 6}],
            "task_type": "class",
            "task_identifier": task,
            "ows": {"position": "(1042.0, 234.0)"},
            "uiProps": {"position": {"x": 1042, "y": 234}},
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

    ows = {
        "annotations": [
            {
                "id": "0",
                "type": "text",
                "params": {
                    "geometry": [92.0, 137.0, 150.0, 67.0],
                    "text": 'Double-click to "trigger" the workflow',
                    "font": {"family": "Ubuntu", "size": 16},
                    "content_type": "text/plain",
                },
            },
            {
                "id": "1",
                "type": "arrow",
                "params": {
                    "geometry": [[222.0, 167.0], [281.0, 168.0]],
                    "color": "#C1272D",
                },
            },
            {
                "id": "2",
                "type": "text",
                "params": {
                    "geometry": [84.0, 299.0, 150.0, 68.0],
                    "text": 'Double-click to\n"trigger" the workflow',
                    "font": {"family": "Ubuntu", "size": 16},
                    "content_type": "text/plain",
                },
            },
            {
                "id": "3",
                "type": "arrow",
                "params": {
                    "geometry": [[217.0, 319.0], [275.0, 319.0]],
                    "color": "#C1272D",
                },
            },
            {
                "id": "4",
                "type": "text",
                "params": {
                    "geometry": [369.0, 10.0, 499.0, 68.0],
                    "text": 'Double-click any node to see the\n - "Execute" button: execute only the task\n - "Trigger" button: execute the task and all downstream tasks',
                    "font": {"family": "Ubuntu", "size": 16},
                    "content_type": "text/plain",
                },
            },
        ]
    }
    graph = {"id": "acyclic1", "label": "acyclic1", "schema_version": "1.1", "ows": ows}

    taskgraph = {"graph": graph, "links": links, "nodes": nodes}

    expected_results = {
        "task1": {"result": 1},
        "task2": {"result": 2},
        "task3": {"result": 4},
        "task4": {"result": 6},
        "task5": {"result": 10},
        "task6": {"result": 16},
    }

    return taskgraph, expected_results
