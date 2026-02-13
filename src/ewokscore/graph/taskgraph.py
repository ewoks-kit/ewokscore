from typing import Hashable, Optional, Union
import networkx
from ewoksutils.import_utils import qualname

from .. import inittask
from .subgraph import extract_graph_nodes
from .subgraph import add_subgraph_links
from . import analysis
from . import serialize
from .validate import validate_graph
from .multigraph import flatten_multigraph
from .error_handlers import connect_default_error_handlers
from .execute.sequential import execute_graph
from .compare import graphs_are_equal


def load_graph(source=None, representation=None, **load_options):
    if isinstance(source, TaskGraph):
        return source
    else:
        return TaskGraph(source=source, representation=representation, **load_options)


def node_has_links(graph, node_id):
    try:
        next(graph.successors(node_id))
    except StopIteration:
        try:
            next(graph.predecessors(node_id))
        except StopIteration:
            return False
    return True


def merge_graphs(graphs, graph_attrs=None, rename_nodes=None, **load_options):
    lst = list()
    if rename_nodes is None:
        rename_nodes = [True] * len(graphs)
    else:
        assert len(graphs) == len(rename_nodes)
    for g, rename in zip(graphs, rename_nodes):
        g = load_graph(g, **load_options)
        gname = repr(g)
        g = g.graph
        if rename:
            mapping = {s: (gname, s) for s in g.nodes}
            g = networkx.relabel_nodes(g, mapping, copy=True)
        lst.append(g)
    ret = load_graph(networkx.compose_all(lst), **load_options)
    if graph_attrs:
        ret.graph.graph.update(graph_attrs)
    return ret


def get_subgraphs(graph: networkx.DiGraph, **load_options):
    subgraphs = dict()
    for node_id, node_attrs in graph.nodes.items():
        task_type, task_info = inittask.task_executable_info(
            node_id, node_attrs, all=True
        )
        if task_type == "graph":
            g = load_graph(task_info["task_identifier"], **load_options)
            g.graph.graph["id"] = node_id
            node_label = node_attrs.get("label")
            if node_label:
                g.graph.graph["label"] = node_label
            subgraphs[node_id] = g
    return subgraphs


class TaskGraph:
    """The API for graph analysis is provided by `networkx`.
    Any directed graph is supported (cyclic or acyclic).

    Loop over the dependencies of a task

    .. code-block:: python

        for source in taskgraph.predecessors(target):
            link_attrs = taskgraph.graph[source][target]

    Loop over the tasks dependent on a task

    .. code-block:: python

        for target in taskgraph.successors(source):
            link_attrs = taskgraph.graph[source][target]

    For acyclic graphs, sequential task execution can be done like this:

    .. code-block:: python

        taskgraph.execute()
    """

    def __init__(self, source=None, representation=None, **load_options):
        self.load(source=source, representation=representation, **load_options)

    def __repr__(self):
        return self.graph_label

    @property
    def graph_id(self) -> Hashable:
        return self.graph.graph.get("id", qualname(type(self)))

    @property
    def graph_label(self) -> str:
        return self.graph.graph.get("label", self.graph_id)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError(other, type(other))
        return graphs_are_equal(self.graph, other.graph)

    def load(
        self,
        source=None,
        representation: Optional[Union[serialize.GraphRepresentation, str]] = None,
        subgraph_representation: Optional[
            Union[serialize.GraphRepresentation, str]
        ] = None,
        **load_options,
    ) -> None:
        graph = serialize.load(
            source=source, representation=representation, **load_options
        )

        if subgraph_representation is not None:
            representation = subgraph_representation

        subgraphs = get_subgraphs(graph, representation=representation, **load_options)
        if subgraphs:
            # Extract
            edges, update_attrs = extract_graph_nodes(graph, subgraphs)
            graph = flatten_multigraph(graph)

            # Merged
            self.graph = graph
            graphs = [self] + list(subgraphs.values())
            rename_nodes = [False] + [True] * len(subgraphs)
            graph = merge_graphs(
                graphs,
                graph_attrs=graph.graph,
                rename_nodes=rename_nodes,
                **load_options,
            ).graph

            # Re-link
            add_subgraph_links(graph, edges, update_attrs)

        graph = flatten_multigraph(graph)
        connect_default_error_handlers(graph)
        validate_graph(graph)
        self.graph = graph

    def dump(
        self,
        destination=None,
        representation: Optional[Union[serialize.GraphRepresentation, str]] = None,
        **kw,
    ) -> Optional[Union[str, dict]]:
        return serialize.dump(
            self.graph, destination=destination, representation=representation, **kw
        )

    def serialize(self) -> str:
        return self.dump(representation=serialize.GraphRepresentation.json_string)

    @property
    def is_cyclic(self) -> bool:
        return analysis.graph_is_cyclic(self.graph)

    @property
    def has_conditional_links(self) -> bool:
        return analysis.graph_has_conditional_links(self.graph)

    def execute(self, *args, **kw):
        return execute_graph(self.graph, *args, **kw)
