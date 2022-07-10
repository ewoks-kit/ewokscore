import networkx

from ..utils import dict_merge


def flatten_multigraph(graph: networkx.DiGraph) -> networkx.DiGraph:
    """The attributes of links between the same two nodes are merged."""
    if not graph.is_multigraph():
        return graph
    newgraph = networkx.DiGraph(**graph.graph)

    edgeattrs = dict()
    for edge, attrs in graph.edges.items():
        key = edge[:2]
        mergedattrs = edgeattrs.setdefault(key, dict())
        # mergedattrs["links"] and attrs["links"]
        # could be two sequences that need to be concatenated
        dict_merge(mergedattrs, attrs, contatenate_sequences=True)

    for name, attrs in graph.nodes.items():
        newgraph.add_node(name, **attrs)
    for (source_id, target_id), mergedattrs in edgeattrs.items():
        newgraph.add_edge(source_id, target_id, **mergedattrs)
    return newgraph
