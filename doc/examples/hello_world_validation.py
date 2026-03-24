from typing import Optional
from typing import Union

from pydantic import Field
from pydantic import model_validator

from ewokscore import execute_graph
from ewokscore.task import BaseInputModel
from ewokscore.task import BaseOutputModel
from ewokscore.task import Task

NumberOrStr = Union[int, float, str]


# Define task signature
class InputModel(BaseInputModel):
    a: NumberOrStr = Field(
        ..., description="First argument to sum.", examples=[10.5, "hello"]
    )
    b: Optional[NumberOrStr] = Field(
        None, description="Second argument to sum.", examples=[20.1, " world"]
    )

    @model_validator(mode="after")
    def check_compatible_types(self):
        if self.b is not None and (isinstance(self.a, str) ^ isinstance(self.b, str)):
            raise ValueError(
                "a and b must be of compatible types (both numbers or both strings)"
            )
        return self


class OutputModel(BaseOutputModel):
    result: NumberOrStr = Field(
        ..., description="Result of the sum.", examples=[30.6, "hello world"]
    )


# Implement a workflow task
class SumTask(Task, input_model=InputModel, output_model=OutputModel):
    def run(self):
        result = self.inputs.a
        if self.inputs.b is not None:
            result += self.inputs.b
        self.outputs.result = result


# Define a workflow with default inputs
graph = {"id": "testworkflow", "schema_version": "1.1"}
nodes = [
    {
        "id": "task1",
        "task_type": "class",
        "task_identifier": "__main__.SumTask",
        "default_inputs": [{"name": "a", "value": 1}],
    },
    {
        "id": "task2",
        "task_type": "class",
        "task_identifier": "__main__.SumTask",
        "default_inputs": [{"name": "b", "value": 1}],
    },
    {
        "id": "task3",
        "task_type": "class",
        "task_identifier": "__main__.SumTask",
        "default_inputs": [{"name": "b", "value": 1}],
    },
]
links = [
    {
        "source": "task1",
        "target": "task2",
        "data_mapping": [{"source_output": "result", "target_input": "a"}],
    },
    {
        "source": "task2",
        "target": "task3",
        "data_mapping": [{"source_output": "result", "target_input": "a"}],
    },
]
workflow = {"graph": graph, "nodes": nodes, "links": links}

# Define task inputs
inputs = [{"id": "task1", "name": "a", "value": 10}]

# Execute a workflow (use a proper Ewoks task scheduler in production)
varinfo = {"root_uri": "/tmp/myresults"}  # optionally save all task outputs
result = execute_graph(workflow, varinfo=varinfo, inputs=inputs)
print(result)
