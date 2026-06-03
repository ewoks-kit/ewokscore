from ewokscore import execute_graph
import pytest


def test_sequence_matcher_missing_required_inputs():
    with pytest.raises(ValueError, match="you got 'valufe'. Could this be a typo?"):
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


def test_sequence_matcher_typo_required_inputs():
    with pytest.raises(
        ValueError,
        match="The required key 'list' is missing and you provide 'listx'. Could this be a typo?",
    ):
        _ = execute_graph(
            graph={
                "graph": {"id": "test"},
                "nodes": [
                    {
                        "id": "sumlist1",
                        "task_type": "class",
                        "task_identifier": "ewokscore.tests.examples.tasks.sumlist.SumList",
                    }
                ],
            },
            inputs=[
                {
                    "id": "sumlist1",
                    "name": "listx",
                    "value": [1, 2, 3],
                },
            ],
        )


def test_sequence_matcher_typo_optional_inputs(caplog):
    with caplog.at_level("WARNING", logger="ewokscore.task"):
        _ = execute_graph(
            graph={
                "graph": {"id": "test"},
                "nodes": [
                    {
                        "id": "sumlist1",
                        "task_type": "class",
                        "task_identifier": "ewokscore.tests.examples.tasks.sumlist.SumList",
                    }
                ],
            },
            inputs=[
                {
                    "id": "sumlist1",
                    "name": "list",
                    "value": [1, 2, 3],
                },
                {
                    "id": "sumlist1",
                    "name": "delayx",
                    "value": 1,
                },
            ],
        )
    assert (
        "The optional key 'delay' is missing and you provide 'delayx'. Could this be a typo?"
        in caplog.text
    )
