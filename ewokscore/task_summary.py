import json
import logging
from pathlib import Path
from .task import Task

logger = logging.getLogger(__name__)


def generate_task_summary() -> dict:
    summary = list()
    for cls in Task.get_subclasses():
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
