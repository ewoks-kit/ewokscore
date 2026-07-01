import networkx


def v0_update(graph: networkx.DiGraph) -> None:
    """Outdated version"""
    raise RuntimeError("not supported")


def from_v1_0_to_v1_1(graph: networkx.DiGraph) -> None:
    """This version does not have the requirements field."""
    graph.graph["schema_version"] = "1.1"


def from_v1_1_to_v1_2(graph: networkx.DiGraph) -> None:
    """
    v1.1 does not have the __ewoks_serialize__ field.
    It does not support the following link attributes:
     - `cache_if_not_required`
     - `required` when set explicitly to `False`, ignoring graph analysis
    """
    graph.graph["schema_version"] = "1.2"
