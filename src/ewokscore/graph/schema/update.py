import networkx


def v0_update(graph: networkx.DiGraph) -> None:
    """Outdated version"""
    raise RuntimeError("not supported")


def from_v1_0_to_v1_1(graph: networkx.DiGraph) -> None:
    """This version does not have the requirements field."""
    graph.graph["schema_version"] = "1.1"
