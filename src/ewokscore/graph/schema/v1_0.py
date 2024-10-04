import networkx


def update_graph_schema(graph: networkx.DiGraph) -> None:
    """This version does not have the requirements field."""
    graph.graph["schema_version"] = "1.1"
