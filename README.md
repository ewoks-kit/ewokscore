# EwoksCore: API for graphs and tasks in Ewoks

## Install

```bash
python -m pip install ewokscore[test]
```

## Test

```bash
pytest --pyargs ewokscore.tests
```

## Getting started

```python
from ewokscore import Task
from ewokscore import execute_graph

# Implement a workflow task
class SumTask(
    Task, input_names=["a"], optional_input_names=["b"], output_names=["result"]
):
    def run(self):
        result = self.inputs.a
        if self.inputs.b:
            result += self.inputs.b
        self.outputs.result = result


# Define a workflow
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
        "data_mapping": [{"target_input": "a", "source_output": "result"}],
    },
    {
        "source": "task2",
        "target": "task3",
        "data_mapping": [{"target_input": "a", "source_output": "result"}],
    },
]
workflow = {"nodes": nodes, "links": links}

# Execute a workflow (use a proper Ewoks task scheduler in production)
varinfo = {"root_uri": "/tmp/myresults"}  # optional
tasks = execute_graph(workflow, varinfo=varinfo)
print(tasks["task3"].output_values)
```

## Documentation

https://workflow.gitlab-pages.esrf.fr/ewoks/ewokscore
