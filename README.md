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
from ewokscore import load_graph

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
    {"id": "task1", "class": "__main__.SumTask", "inputs": {"a": 1}},
    {"id": "task2", "class": "__main__.SumTask", "inputs": {"b": 1}},
    {"id": "task3", "class": "__main__.SumTask", "inputs": {"b": 1}},
]
links = [
    {"source": "task1", "target": "task2", "arguments": {"a": "result"}},
    {"source": "task2", "target": "task3", "arguments": {"a": "result"}},
]
workflow = {"nodes": nodes, "links": links}

# Execute a workflow (use a proper Ewoks task scheduler in production)
graph = load_graph(workflow)
varinfo = {"root_uri": "/tmp/myresults"}  # optional
tasks = graph.execute(varinfo=varinfo)
print(tasks["task3"].output_values)
```

## Documentation

https://workflow.gitlab-pages.esrf.fr/ewoks/ewokscore
