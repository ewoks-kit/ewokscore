from typing import Any
from pprint import pprint
import logging

from ewokscore.bindings import load_graph


logger = logging.getLogger(__file__)


def extract_requirements(workflow: Any):
    imports: set[str] = set()
    graph = load_graph(workflow)

    for node_id, node in graph.graph.nodes.items():
        task_identifier = node["task_identifier"]
        task_type = node["task_type"]

        if task_type == "class":
            package = task_identifier.split(".")[0]
            if package == "__main__" or "":
                logger.warning(
                    f"Could not extract requirements for node {node_id}: the task identifier is a relative import or a import from __main__."
                )
                continue

            imports.add(package)
        elif task_type.startswith("ppf"):
            imports.add("ewoksppf")
            logger.warning(
                f"Requirement extraction may be incomplete for node {node_id}: {task_type} is only partially supported."
            )
        else:
            logger.warning(
                f"Could not extract requirements for node {node_id}: unsupported task type {task_type}."
            )

    return list(imports)


if __name__ == "__main__":
    import sys

    requirements = extract_requirements(sys.argv[1])
    pprint(requirements)
