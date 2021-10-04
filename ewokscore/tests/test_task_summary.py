from ewokscore.task_summary import generate_task_summary
from .examples.tasks.sumtask import SumTask


def test_graph_summary():
    summary = generate_task_summary()
    names = [s["task_identifier"] for s in summary]
    assert SumTask.class_registry_name() in names
