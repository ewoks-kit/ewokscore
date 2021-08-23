from typing import Callable, Optional
from .task import Task
from .utils import import_method


_GENERATORS = dict()


def get_task_class_generator(generator_qualname: str) -> Callable[[str], Task]:
    if not generator_qualname:
        return Task.get_subclass
    task_class_generator = _GENERATORS.get(generator_qualname, None)
    if task_class_generator is not None:
        return task_class_generator
    task_class_generator = import_method(generator_qualname)
    _GENERATORS[generator_qualname] = task_class_generator
    return task_class_generator


def get_dynamically_task_class(
    generator_qualname: Optional[str], registry_name: str
) -> Task:
    return get_task_class_generator(generator_qualname)(registry_name)
