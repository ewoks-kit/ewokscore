from typing import List

from ...graph import load_graph
from ...graph._analysis import GraphAnalysis

METHOD_TASK = "dummy"
CLASS_TASK = "ewokscore.tests.examples.tasks.sumtask.SumTask"

TRUE = [{"source_output": "result", "value": True}]
FALSE = [{"source_output": "result", "value": False}]


def node(node_id: str, **attrs) -> dict:
    return {
        "id": node_id,
        "task_type": "method",
        "task_identifier": METHOD_TASK,
        **attrs,
    }


def class_node(node_id: str, **attrs) -> dict:
    return {
        "id": node_id,
        "task_type": "class",
        "task_identifier": CLASS_TASK,
        **attrs,
    }


def analysis(nodes: List[dict], links: List[dict]) -> GraphAnalysis:
    """Load a graph and return its analysis."""
    return load_graph(
        {
            "graph": {"id": "test", "schema_version": "1.2"},
            "nodes": nodes,
            "links": links,
        }
    ).analysis


def chain(*node_ids: str, **link_attrs) -> List[dict]:
    """Links connecting the nodes one after the other."""
    return [
        {"source": source_id, "target": target_id, **link_attrs}
        for source_id, target_id in zip(node_ids, node_ids[1:])
    ]
