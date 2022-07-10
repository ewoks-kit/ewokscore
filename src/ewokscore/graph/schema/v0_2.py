import networkx


def update_graph_schema(graph: networkx.DiGraph) -> None:
    """This version is for testing"""
    graph.graph["schema_version"] = "1.0"
