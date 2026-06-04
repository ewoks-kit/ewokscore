import pytest

from ewokscore import execute_graph


def test_matcher_input_typo():
    with pytest.raises(
        ValueError,
        match=r"(?s)(?=.*Did you mean 'value'\?)(?=.*Did you mean 'name'\?)",
    ):
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
                    "namze": "a",
                    "valufe": 1,
                },
            ],
        )


def test_matcher_typo_required_inputs():
    with pytest.raises(
        ValueError,
        match="You provided 'listx'. Did you mean 'list'?",
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


def test_matcher_typo_optional_inputs(caplog):
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
    assert "You provided 'delayx'. Did you mean 'delay'?" in caplog.text


def test_matcher_typo_required_default_inputs():
    with pytest.raises(
        ValueError,
        match="You provided 'listx'. Did you mean 'list'?",
    ):
        _ = execute_graph(
            graph={
                "graph": {"id": "test"},
                "nodes": [
                    {
                        "id": "sumlist1",
                        "task_type": "class",
                        "task_identifier": "ewokscore.tests.examples.tasks.sumlist.SumList",
                        "default_inputs": [
                            {
                                "name": "listx",
                                "value": [1, 2, 3],
                            },
                        ],
                    }
                ],
            },
        )


def test_matcher_typo_optional_default_inputs(caplog):
    with caplog.at_level("WARNING", logger="ewokscore.task"):
        _ = execute_graph(
            graph={
                "graph": {"id": "test"},
                "nodes": [
                    {
                        "id": "sumlist1",
                        "task_type": "class",
                        "task_identifier": "ewokscore.tests.examples.tasks.sumlist.SumList",
                        "default_inputs": [
                            {
                                "name": "list",
                                "value": [1, 2, 3],
                            },
                            {
                                "name": "delayx",
                                "value": 1,
                            },
                        ],
                    }
                ],
            },
        )
    assert "You provided 'delayx'. Did you mean 'delay'?" in caplog.text
