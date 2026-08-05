from pathlib import Path
from typing import Dict
from typing import Hashable
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

import networkx
from ewoksutils.deprecation_utils import deprecated
from ewoksutils.import_utils import qualname

from .. import inittask
from .._serialization.common.utils.types import GraphSerializer
from . import serialize
from ._analysis import GraphAnalysis
from ._freeze import FrozenDiGraph
from .compare import graphs_are_equal
from .error_handlers import connect_default_error_handlers
from .execute.sequential import execute_graph
from .models import GraphSource
from .multigraph import flatten_multigraph
from .subgraph import add_subgraph_links
from .subgraph import extract_graph_nodes
from .validate import validate_graph


class TaskGraph:
    """Any directed graph is supported (cyclic or acyclic).

    Graph analysis (node, link and whole-graph properties derived from the
    graph structure) is provided by `analysis`.

    Loop over the dependencies of a task

    .. code-block:: python

        for source in taskgraph.analysis.node_predecessors(target):
            link_attrs = taskgraph.graph[source][target]

    Loop over the tasks dependent on a task

    .. code-block:: python

        for target in taskgraph.analysis.node_successors(source):
            link_attrs = taskgraph.graph[source][target]

    For acyclic graphs, sequential task execution can be done like this:

    .. code-block:: python

        taskgraph.execute()
    """

    def __init__(
        self,
        source: Optional[GraphSource] = None,
        representation: Optional[Union[serialize.GraphRepresentation, str]] = None,
        root_dir: Optional[Union[str, Path]] = None,
        root_module: Optional[str] = None,
    ):
        self.load(
            source=source,
            representation=representation,
            root_dir=root_dir,
            root_module=root_module,
        )

    def __repr__(self):
        return self.graph_label

    @property
    def graph(self) -> FrozenDiGraph:
        return self._analysis.graph

    @property
    def graph_id(self) -> Hashable:
        return self.graph.graph.get("id", qualname(type(self)))

    @property
    def graph_label(self) -> str:
        return str(self.graph.graph.get("label", self.graph_id))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError(other, type(other))
        return graphs_are_equal(self.graph, other.graph)

    def load(
        self,
        source: Optional[GraphSource] = None,
        representation: Optional[Union[serialize.GraphRepresentation, str]] = None,
        subgraph_representation: Optional[
            Union[serialize.GraphRepresentation, str]
        ] = None,
        root_dir: Optional[Union[str, Path]] = None,
        root_module: Optional[str] = None,
    ) -> None:
        graph = serialize.load(
            source=source,
            representation=representation,
            root_dir=root_dir,
            root_module=root_module,
        )

        if subgraph_representation is not None:
            representation = subgraph_representation

        subgraphs, subgraph_names = get_subgraphs(
            graph,
            representation=representation,
            root_dir=root_dir,
            root_module=root_module,
        )
        if subgraphs:
            # Extract
            edges, update_attrs = extract_graph_nodes(graph, subgraphs)
            graph = flatten_multigraph(graph)

            # Merged
            self._analysis = GraphAnalysis(graph)
            graphs = [self] + list(subgraphs.values())
            rename_nodes = [False] + [True] * len(subgraphs)
            names = [None] + [subgraph_names[node_id] for node_id in subgraphs]
            merged_graph = merge_graphs(
                graphs,
                graph_attrs=graph.graph,
                rename_nodes=rename_nodes,
                names=names,
                representation=representation,
                root_dir=root_dir,
                root_module=root_module,
            ).graph

            # `merged_graph` is frozen (it went through `load` already):
            # unfreeze it since `add_subgraph_links` still needs to mutate it.
            graph = networkx.DiGraph(merged_graph)

            # Re-link
            add_subgraph_links(graph, edges, update_attrs)

        graph = flatten_multigraph(graph)
        connect_default_error_handlers(graph)
        validate_graph(graph)
        self._analysis = GraphAnalysis(graph)

    def dump(
        self,
        destination: Optional[Union[str, Path]] = None,
        representation: Optional[Union[serialize.GraphRepresentation, str]] = None,
        serializer: Optional[Union[GraphSerializer, str]] = None,
        **save_options,
    ) -> Union[str, Path, dict]:
        return serialize.dump(
            self.graph,
            destination=destination,
            representation=representation,
            serializer=serializer,
            **save_options,
        )

    def serialize(
        self, serializer: Optional[Union[GraphSerializer, str]] = None
    ) -> str:
        return self.dump(
            representation=serialize.GraphRepresentation.json_string,
            serializer=serializer,
        )

    @property
    def analysis(self) -> GraphAnalysis:
        """Graph analysis with all derived node and link properties cached.

        Assumes `graph` is not modified after loading.
        """
        return self._analysis

    @property
    def is_cyclic(self) -> bool:
        return self.analysis.graph_is_cyclic()

    @property
    def has_conditional_links(self) -> bool:
        return self.analysis.graph_has_conditional_links()

    def execute(self, *args, **kw):
        kw.setdefault("graph_analysis", self.analysis)
        return execute_graph(self.graph, *args, **kw)

    @property
    def requirements(self) -> Optional[Sequence[str]]:
        requirements = self.graph.graph.get("requirements", None)

        if isinstance(requirements, Sequence):
            return requirements
        return None


def load_graph(
    source: Optional[Union[TaskGraph, GraphSource]] = None,
    representation: Optional[Union[serialize.GraphRepresentation, str]] = None,
    root_dir: Optional[Union[str, Path]] = None,
    root_module: Optional[str] = None,
) -> TaskGraph:
    if isinstance(source, TaskGraph):
        return source
    else:
        return TaskGraph(
            source=source,
            representation=representation,
            root_dir=root_dir,
            root_module=root_module,
        )


@deprecated("'node_has_links' is deprecated and will be removed")
def node_has_links(graph: networkx.DiGraph, node_id: Hashable) -> bool:
    try:
        next(graph.successors(node_id))
    except StopIteration:
        try:
            next(graph.predecessors(node_id))
        except StopIteration:
            return False
    return True


def merge_graphs(
    graphs: Sequence[Union[TaskGraph, GraphSource]],
    graph_attrs: Optional[dict] = None,
    rename_nodes: Optional[Sequence[bool]] = None,
    names: Optional[Sequence[Optional[Hashable]]] = None,
    representation: Optional[Union[serialize.GraphRepresentation, str]] = None,
    root_dir: Optional[Union[str, Path]] = None,
    root_module: Optional[str] = None,
) -> TaskGraph:
    """`names` gives the name to rename nodes under for each graph in `graphs`
    (used instead of `repr(graph)` when not given), and must have the same
    length as `graphs` when provided.
    """
    lst = list()
    if rename_nodes is None:
        rename_nodes = [True] * len(graphs)
    elif len(graphs) != len(rename_nodes):
        raise ValueError("rename_nodes must have the same length as graphs")
    if names is None:
        names = [None] * len(graphs)
    elif len(graphs) != len(names):
        raise ValueError("names must have the same length as graphs")

    for g, rename, name in zip(graphs, rename_nodes, names):
        g = load_graph(
            g, representation=representation, root_dir=root_dir, root_module=root_module
        )
        gname = repr(g) if name is None else str(name)
        g = g.graph
        if rename:
            mapping = {s: (gname, s) for s in g.nodes}
            g = networkx.relabel_nodes(g, mapping, copy=True)
        lst.append(g)

    composed = networkx.compose_all(lst)
    if graph_attrs:
        # `composed` is freshly built by `compose_all`, so its `graph`
        # attribute dict is a plain, unfrozen dict: safe to update in place
        # before `load_graph` below validates and (re)freezes the result.
        composed.graph.update(graph_attrs)
    return load_graph(
        composed,
        representation=representation,
        root_dir=root_dir,
        root_module=root_module,
    )


def get_subgraphs(
    graph: networkx.DiGraph,
    representation: Optional[Union[serialize.GraphRepresentation, str]] = None,
    root_dir: Optional[Union[str, Path]] = None,
    root_module: Optional[str] = None,
) -> Tuple[Dict[Hashable, TaskGraph], Dict[Hashable, Hashable]]:
    """Returns the graph-type nodes of `graph` as loaded sub-graphs, together
    with the name each should be merged under: the calling node's `label`,
    or else its id.
    """
    subgraphs = dict()
    names = dict()
    for node_id, node_attrs in graph.nodes.items():
        task_type, task_info = inittask.task_executable_info(
            node_id, node_attrs, all=True
        )
        if task_type == "graph":
            subgraphs[node_id] = load_graph(
                task_info["task_identifier"],
                representation=representation,
                root_dir=root_dir,
                root_module=root_module,
            )
            names[node_id] = node_attrs.get("label") or node_id
    return subgraphs, names
