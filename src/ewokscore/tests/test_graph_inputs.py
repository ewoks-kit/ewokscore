from copy import deepcopy
from typing import Union

from pydantic import Field

from ..bindings import execute_graph
from ..bindings import load_graph
from ..graph import inputs
from ..graph.taskgraph import TaskGraph
from ..missing_data import MISSING_DATA
from ..model import BaseInputModel
from ..task import Task


def test_shorten_task_identifiers():
    task_identifiers = ["a.b.c", "a.b.d", "a.b.e"]
    shortmap = inputs._shorten_task_identifiers(task_identifiers)
    expected = {"a.b.c": "c", "a.b.d": "d", "a.b.e": "e"}
    assert shortmap == expected

    task_identifiers = ["a.b.c", "a.b.d", "a.bb.c"]
    shortmap = inputs._shorten_task_identifiers(task_identifiers)
    expected = {"a.b.c": "b.c", "a.b.d": "d", "a.bb.c": "bb.c"}
    assert shortmap == expected

    task_identifiers = ["a.b.c", "a.b.c", "a.bb.c"]
    shortmap = inputs._shorten_task_identifiers(task_identifiers)
    expected = {"a.b.c": "b.c", "a.bb.c": "bb.c"}
    assert shortmap == expected


def test_graph_inputs():
    graph = create_graph()
    node_inputs = inputs.graph_inputs(graph)

    expected = [
        inputs.NodeInput(
            id="task1",
            label=None,
            task_identifier="ClassExample",
            name="a",
            value=1,
            required=True,
            description=None,
            examples=None,
            import_error=None,
        ),
        inputs.NodeInput(
            id="task1",
            label=None,
            task_identifier="ClassExample",
            name="b",
            value=MISSING_DATA,
            required=True,
            description=None,
            examples=None,
            import_error=None,
        ),
        inputs.NodeInput(
            id="task1",
            label=None,
            task_identifier="ClassExample",
            name="c",
            value=MISSING_DATA,
            required=False,
            description=None,
            examples=None,
            import_error=None,
        ),
        inputs.NodeInput(
            id="task1",
            label=None,
            task_identifier="ClassExample",
            name="d",
            value=MISSING_DATA,
            required=False,
            description=None,
            examples=None,
            import_error=None,
        ),
        inputs.NodeInput(
            id="task2",
            label="task2 label",
            task_identifier="ClassExampleWithModel",
            name="c",
            value=4,
            required=False,
            description="parameter c",
            examples=None,
            import_error=None,
        ),
        inputs.NodeInput(
            id="task2",
            label="task2 label",
            task_identifier="ClassExampleWithModel",
            name="d",
            value=-2,
            required=False,
            description=None,
            examples=[100, "word"],
            import_error=None,
        ),
        inputs.NodeInput(
            id="task3",
            label=None,
            task_identifier="method_example",
            name="e",
            value=5,
            required=True,
            description=None,
            examples=None,
            import_error=None,
        ),
        inputs.NodeInput(
            id="task3",
            label=None,
            task_identifier="method_example",
            name="g",
            value=MISSING_DATA,
            required=True,
            description=None,
            examples=None,
            import_error=None,
        ),
        inputs.NodeInput(
            id="task3",
            label=None,
            task_identifier="method_example",
            name="f",
            value=-3,
            required=False,
            description=None,
            examples=None,
            import_error=None,
        ),
        inputs.NodeInput(
            id="task4",
            label=None,
            task_identifier="NonExistingClass",
            name="guess",
            value=999,
            required=True,
            description=None,
            examples=None,
            import_error=ModuleNotFoundError("No module named 'does'"),
        ),
    ]

    # Patch exceptions for comparison
    for node_input in node_inputs:
        if node_input.import_error:
            node_input.import_error = repr(node_input.import_error)
    for node_input in expected:
        if node_input.import_error:
            node_input.import_error = repr(node_input.import_error)

    assert node_inputs == expected


def test_graph_inputs_as_table():
    graph = create_graph()
    column_names, rows, metadata, footnotes = inputs.graph_inputs_as_table(graph)

    expected_column_names = [
        "Name",
        "Value",
        "Description",
        "Examples",
        "Task identifier",
        "Id",
        "Label",
    ]
    expected_rows = [
        ["b⁽*⁾", "<MISSING_DATA>", "", "", "ClassExample", "task1", ""],
        ["g⁽*⁾", "<MISSING_DATA>", "", "", "method_example", "task3", ""],
        ["a", "1", "", "", "ClassExample", "task1", ""],
        ["c", "<MISSING_DATA>", "", "", "ClassExample", "task1", ""],
        ["d", "<MISSING_DATA>", "", "", "ClassExample", "task1", ""],
        ["c", "4", "parameter c", "", "ClassExampleWithModel", "task2", "task2 label"],
        [
            "d",
            "-2",
            "",
            "• 100\n• 'word'",
            "ClassExampleWithModel",
            "task2",
            "task2 label",
        ],
        ["e", "5", "", "", "method_example", "task3", ""],
        ["f", "-3", "", "", "method_example", "task3", ""],
        ["guess⁽†⁾", "999", "", "", "NonExistingClass", "task4", ""],
    ]
    expected_metadata = {"id": "testgraph", "description": "Test graph inputs"}
    expected_footnotes = [
        "⁽*⁾ Value is required for execution.",
        "⁽†⁾ Information from workflow only (task cannot be imported).",
    ]

    assert rows == expected_rows
    assert column_names == expected_column_names
    assert metadata == expected_metadata
    assert footnotes == expected_footnotes


class ClassExample(
    Task,
    input_names=["a", "b"],
    optional_input_names=["c", "d"],
    output_names=["a", "b", "c", "d"],
):
    def run(self):
        self.outputs.a = self.inputs.a
        self.outputs.b = self.inputs.b
        self.outputs.c = self.get_input_value("c", -1)
        self.outputs.d = self.get_input_value("d", -2)


class InputModel(BaseInputModel):
    a: Union[int, str] = Field(...)
    a: Union[int, str] = Field(...)
    c: Union[int, str] = Field(-1, description="parameter c")
    d: Union[int, str] = Field(-2, examples=[100, "word"])


class ClassExampleWithModel(
    Task,
    input_model=InputModel,
    output_names=["a", "b", "c", "d"],
):
    def run(self):
        self.outputs.a = self.inputs.a
        self.outputs.b = self.inputs.b
        self.outputs.c = self.inputs.c
        self.outputs.d = self.inputs.d


def method_example(a, b, e, g, c=-1, d=-2, f=-3):
    return {"a": a, "b": b, "c": c, "d": d, "e": e, "f": f, "g": g}


def create_graph() -> TaskGraph:
    graph = {"id": "testgraph", "schema_version": "1.1", "label": "Test graph inputs"}
    nodes = [
        {
            "id": "task1",
            "default_inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": f"{__name__}.ClassExample",
        },
        {
            "id": "task2",
            "label": "task2 label",
            "default_inputs": [{"name": "b", "value": 3}, {"name": "c", "value": 4}],
            "task_type": "class",
            "task_identifier": f"{__name__}.ClassExampleWithModel",
        },
        {
            "id": "task3",
            "default_inputs": [{"name": "e", "value": 5}],
            "task_type": "method",
            "task_identifier": f"{__name__}.method_example",
        },
    ]

    links = [
        {
            "source": "task1",
            "target": "task2",
            "data_mapping": [{"source_output": "b", "target_input": "a"}],
        },
        {
            "source": "task2",
            "target": "task3",
            "map_all_data": True,
        },
    ]

    graph_dict = {"graph": graph, "links": links, "nodes": nodes}
    result = execute_graph(
        deepcopy(graph_dict),
        merge_outputs=False,
        inputs=[
            {"id": "task1", "name": "b", "value": 2},
            {"id": "task3", "name": "e", "value": 5},
            {"id": "task3", "name": "g", "value": 6},
        ],
        outputs=[{"all": True}],
    )
    expected = {
        "task1": {"a": 1, "b": 2, "c": -1, "d": -2},
        "task2": {"a": 2, "b": 3, "c": 4, "d": -2},
        "task3": {
            "return_value": {"a": 2, "b": 3, "c": 4, "d": -2, "e": 5, "g": 6, "f": -3}
        },
    }
    assert result == expected

    nodes.append(
        {
            "id": "task4",
            "default_inputs": [{"name": "guess", "value": 999}],
            "task_type": "class",
            "task_identifier": "does.not.exists.NonExistingClass",
        }
    )

    task_graph = load_graph(graph_dict)
    return task_graph
