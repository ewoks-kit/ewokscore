from ewokscore import execute_graph
import pytest


def test_sequence_matcher_missing_required_inputs():
    with pytest.raises(ValueError, match="Could this be a typo?"):
        _ = execute_graph(
            graph={
                "graph": {"id": "test"},
                "nodes": [
                    {
                        "id": "sum1",
                        "task_type": "class",
                        "task_identifier": "ewokscore.tests.examples.tasks.sumtask.SumTask",
                    }
                ],
            },
            inputs=[
                {
                    "id": "sum1",
                    "name": "a",
                    "valufe": 1,
                },
            ],
        )
