from collections import defaultdict

import networkx

from ..conditions import DEFAULT_CONDITION_OPERATOR
from ..conditions import condition_values_equal


def v0_update(graph: networkx.DiGraph) -> None:
    """Outdated version"""
    raise RuntimeError("not supported")


def from_v1_0_to_v1_1(graph: networkx.DiGraph) -> None:
    """This version does not have the requirements field."""
    graph.graph["schema_version"] = "1.1"


def from_v1_1_to_v1_2(graph: networkx.DiGraph) -> None:
    """This version does not have conditional link operators."""
    _migrate_conditions_else_value(graph)
    graph.graph["schema_version"] = "1.2"


def _migrate_conditions_else_value(graph: networkx.DiGraph) -> None:
    for source_id, node_attrs in graph.nodes.items():
        if "conditions_else_value" not in node_attrs:
            continue

        conditions_else_value = node_attrs.get("conditions_else_value", None)
        covered_values = defaultdict(list)
        else_conditions = []

        for target_id in graph.successors(source_id):
            for condition in graph[source_id][target_id].get("conditions", list()):
                if (
                    condition.get("operator", DEFAULT_CONDITION_OPERATOR)
                    != DEFAULT_CONDITION_OPERATOR
                ):
                    continue
                source_output = condition["source_output"]
                if condition_values_equal(condition["value"], conditions_else_value):
                    else_conditions.append(condition)
                else:
                    condition["operator"] = DEFAULT_CONDITION_OPERATOR
                    values = covered_values[source_output]
                    if not any(
                        condition_values_equal(condition["value"], value)
                        for value in values
                    ):
                        values.append(condition["value"])

        for condition in else_conditions:
            source_output = condition["source_output"]
            condition["operator"] = "not_in"
            condition["value"] = list(covered_values.get(source_output, list()))
