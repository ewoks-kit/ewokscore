from ewoksutils.import_utils import qualname

from ..inittask import instantiate_task
from ..task import Task


def task_class_generator(qualname):
    registry_name = qualname
    if registry_name in Task.get_subclass_names():
        return Task.get_subclass(qualname)

    class DynamicTask(Task, output_names=["result"], registry_name=registry_name):
        def run(self):
            self.outputs.result = qualname

    return DynamicTask


def test_task_class_generator():
    task_name = "some.unique.task.name"
    task = instantiate_task(
        "node_id",
        {
            "task_type": "generated",
            "task_identifier": task_name,
            "task_generator": qualname(task_class_generator),
        },
    )
    task.execute()
    assert task.get_output_values() == {"result": task_name}
