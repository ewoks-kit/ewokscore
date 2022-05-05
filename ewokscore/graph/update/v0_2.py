import networkx


def update_graph(graph: networkx.DiGraph) -> None:
    """This version is for testing"""
    graph.graph["version"] = "1.0"
