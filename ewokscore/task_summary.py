import json
import logging
import importlib
from typing import List, Iterable
from pathlib import Path
from .task import Task

logger = logging.getLogger(__name__)


def generate_task_summary(*module_names: Iterable[str]) -> List[dict]:
    filter_packages = set()
    for module_name in module_names:
        importlib.import_module(module_name)
        filter_packages.add(module_name.partition(".")[0])
    summary = list()
    for cls in Task.get_subclasses():
        if filter_packages:
            package = cls.__module__.partition(".")[0]
            if package not in filter_packages:
                continue
        task_identifier = cls.class_registry_name()
        category = task_identifier.split(".")[0]
        info = {
            "task_type": "class",
            "task_identifier": task_identifier,
            "required_input_names": list(cls.required_input_names()),
            "optional_input_names": list(cls.optional_input_names()),
            "output_names": list(cls.output_names()),
            "category": category,
        }
        summary.append(info)
    return summary


def save_task_summary(filename, indent=2):
    summary = generate_task_summary()
    if not summary:
        logger.warning(f"No tasks to be saved in {filename}")
        return
    filename = Path(filename).with_suffix(".json")
    with open(filename, "w") as fh:
        json.dump(summary, fh, indent=indent)
