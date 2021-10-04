from .task import Task


def generate_task_summary() -> dict:
    summary = list()
    for cls in Task.get_subclasses():
        info = {
            "task_type": "class",
            "task_identifier": cls.class_registry_name(),
            "required_input_names": list(cls.required_input_names()),
            "optional_input_names": list(cls.optional_input_names()),
            "output_names": list(cls.output_names()),
        }
        summary.append(info)
    return summary
