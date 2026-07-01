from . import graph


@graph
def with_schema():
    graph = {
        "id": "with_schema",
        "label": "with_schema",
        "schema_version": "1.3",
        "workflow_input_schema": {
            "properties": {
                "a": {
                    "type": "number",
                    "x_ewoks_targets": [{"name": "a", "id": "task1a"}],
                },
                "b": {
                    "type": "number",
                    "default": 0,
                    "x_ewoks_targets": [{"name": "b", "id": "task1b"}],
                },
            },
            "required": ["a"],
        },
        "workflow_output_schema": {
            "properties": {
                "result_sum": {
                    "type": "number",
                    "x_ewoks_targets": [{"name": "result", "id": "task"}],
                },
            },
        },
    }

    nodes = [
        {
            "id": "task1a",
            "task_type": "class",
            "task_identifier": "ewokscore.tests.examples.tasks.sumlist.SumList",
            "default_inputs": [{"name": "list", "value": [0, 1, 2]}],
        },
        {
            "id": "task1b",
            "task_type": "class",
            "task_identifier": "ewokscore.tests.examples.tasks.sumtask.SumTask",
            "default_inputs": [{"name": "a", "value": 10}],
        },
        {
            "id": "task2",
            "task_type": "class",
            "task_identifier": "ewokscore.tests.examples.tasks.sumtask.SumTask",
        },
    ]

    links = [
        {
            "source": "task1a",
            "target": "task2",
            "data_mapping": [{"source_output": "sum", "target_input": "a"}],
        },
        {
            "source": "task1b",
            "target": "task2",
            "data_mapping": [{"source_output": "result", "target_input": "b"}],
        },
    ]

    taskgraph = {"graph": graph, "links": links, "nodes": nodes}

    expected_results = {
        "task1a": {"sum": 3},
        "task1b": {"result": 10},
        "task2": {"result": 13},
    }

    return taskgraph, expected_results
