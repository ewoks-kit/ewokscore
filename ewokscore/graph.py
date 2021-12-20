import os
import enum
import json
from collections import Counter
from collections.abc import Mapping
from typing import Any, Dict, Iterable, List, Optional, Set, Union
import networkx


from . import inittask
from .utils import qualname
from .utils import dict_merge
from .subgraph import extract_graph_nodes
from .subgraph import add_subgraph_links
from .task import Task
from .node import NodeIdType
from .node import node_id_from_json
from .node import get_node_label
from . import hashing

CONDITIONS_ELSE_VALUE = "__other__"


def load_graph(source=None, representation=None, **load_options):
    if isinstance(source, TaskGraph):
        return source
    else:
        return TaskGraph(source=source, representation=representation, **load_options)


def set_graph_defaults(graph_as_dict):
    graph_as_dict.setdefault("directed", True)
    graph_as_dict.setdefault("nodes", list())
    graph_as_dict.setdefault("links", list())


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
    for (source, target), mergedattrs in edgeattrs.items():
        newgraph.add_edge(source, target, **mergedattrs)
    return newgraph


def get_subgraphs(graph: networkx.DiGraph, **load_options):
    subgraphs = dict()
    for node_id, node_attrs in graph.nodes.items():
        task_type, task_info = inittask.task_executable_info(
            node_attrs, node_id=node_id, all=True
        )
        if task_type == "graph":
            g = load_graph(task_info["task_identifier"], **load_options)
            g.graph.graph["id"] = node_id
            node_label = node_attrs.get("label")
            if node_label:
                g.graph.graph["label"] = node_label
            subgraphs[node_id] = g
    return subgraphs


def _ewoks_jsonload_hook_pair(item):
    key, value = item
    if key in ("source", "target", "sub_source", "sub_target", "id", "sub_node"):
        value = node_id_from_json(value)
    return key, value


def ewoks_jsonload_hook(items):
    return dict(map(_ewoks_jsonload_hook_pair, items))


def abs_path(path, root_dir=None):
    if os.path.isabs(path):
        return path
    if root_dir:
        path = os.path.join(root_dir, path)
    return os.path.abspath(path)


GraphRepresentation = enum.Enum(
    "GraphRepresentation", "json_file json_dict json_string yaml"
)
NodeIdentifier = enum.Enum("NodeIdentifier", "none id label")


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

    Instantiate a task

    .. code-block:: python

        task = taskgraph.instantiate_task(name, varinfo=varinfo, inputs=inputs)

    For acyclic graphs, sequential task execution can be done like this:

    .. code-block:: python

        taskgraph.execute()
    """

    def __init__(self, source=None, representation=None, **load_options):
        self.load(source=source, representation=representation, **load_options)

    def __repr__(self):
        return self.graph_label

    @property
    def graph_id(self):
        return self.graph.graph.get("id", qualname(type(self)))

    @property
    def graph_label(self):
        return self.graph.graph.get("label", self.graph_id)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError(other, type(other))
        return self.dump() == other.dump()

    def load(
        self,
        source=None,
        representation: Optional[Union[GraphRepresentation, str]] = None,
        root_dir: Optional[str] = None,
    ):
        """From persistent to runtime representation"""
        if isinstance(representation, str):
            representation = GraphRepresentation.__members__[representation]
        if representation is None:
            if isinstance(source, Mapping):
                representation = GraphRepresentation.json_dict
            elif isinstance(source, str):
                if source.endswith(".json"):
                    representation = GraphRepresentation.json_file
                else:
                    representation = GraphRepresentation.json_string
        if not source:
            graph = networkx.DiGraph()
        elif isinstance(source, networkx.Graph):
            graph = source
        elif isinstance(source, TaskGraph):
            graph = source.graph
        elif representation == GraphRepresentation.json_dict:
            set_graph_defaults(source)
            graph = networkx.readwrite.json_graph.node_link_graph(source)
        elif representation == GraphRepresentation.json_file:
            source = abs_path(source, root_dir)
            with open(source, mode="r") as f:
                source = json.load(f, object_pairs_hook=ewoks_jsonload_hook)
            set_graph_defaults(source)
            graph = networkx.readwrite.json_graph.node_link_graph(source)
        elif representation == GraphRepresentation.json_string:
            source = json.loads(source, object_pairs_hook=ewoks_jsonload_hook)
            set_graph_defaults(source)
            graph = networkx.readwrite.json_graph.node_link_graph(source)
        elif representation == GraphRepresentation.yaml:
            source = abs_path(source, root_dir)
            graph = networkx.readwrite.read_yaml(source)
        else:
            raise TypeError(representation, type(representation))

        if not networkx.is_directed(graph):
            raise TypeError(graph, type(graph))

        subgraphs = get_subgraphs(graph, root_dir=root_dir)
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
                root_dir=root_dir,
            ).graph

            # Re-link
            add_subgraph_links(graph, edges, update_attrs)

        self.graph = flatten_multigraph(graph)
        self.validate_graph()

    def dump(
        self,
        destination=None,
        representation: Optional[Union[GraphRepresentation, str]] = None,
        **kw,
    ):
        """From runtime to persistent representation"""
        if isinstance(representation, str):
            representation = GraphRepresentation.__members__[representation]
        if representation is None:
            if isinstance(destination, str) and destination.endswith(".json"):
                representation = GraphRepresentation.json_file
            else:
                representation = GraphRepresentation.json_dict
        if representation == GraphRepresentation.json_dict:
            return networkx.readwrite.json_graph.node_link_data(self.graph)
        elif representation == GraphRepresentation.json_file:
            dictrepr = self.dump()
            with open(destination, mode="w") as f:
                json.dump(dictrepr, f, **kw)
            return destination
        elif representation == GraphRepresentation.json_string:
            dictrepr = self.dump()
            return json.dumps(dictrepr, **kw)
        elif representation == GraphRepresentation.yaml:
            return networkx.readwrite.write_yaml(self.graph, destination, **kw)
        else:
            raise TypeError(representation, type(representation))

    def serialize(self):
        return self.dump(representation=GraphRepresentation.json_string)

    @property
    def is_cyclic(self):
        return not networkx.is_directed_acyclic_graph(self.graph)

    @property
    def has_conditional_links(self):
        for attrs in self.graph.edges.values():
            if attrs.get("conditions") or attrs.get("on_error"):
                return True
        return False

    def instantiate_task(
        self,
        node_id: NodeIdType,
        varinfo: Optional[dict] = None,
        inputs: Optional[dict] = None,
    ) -> Task:
        """Named arguments are dynamic input and Variable config.
        Default input from the persistent representation are added internally.
        """
        # Dynamic input has priority over default input
        nodeattrs = self.graph.nodes[node_id]
        return inittask.instantiate_task(
            nodeattrs, node_id=node_id, varinfo=varinfo, inputs=inputs
        )

    def instantiate_task_static(
        self,
        node_id: NodeIdType,
        tasks: Optional[Dict[Task, int]] = None,
        varinfo: Optional[dict] = None,
        evict_result_counter: Optional[Dict[NodeIdType, int]] = None,
    ) -> Task:
        """Instantiate destination task while no access to the dynamic inputs.
        Side effect: `tasks` will contain all predecessors.
        """
        if self.is_cyclic:
            raise RuntimeError(f"{self} is cyclic")
        if tasks is None:
            tasks = dict()
        if evict_result_counter is None:
            evict_result_counter = dict()
        # Input from previous tasks (instantiate them if needed)
        dynamic_inputs = dict()
        for source_node_id in self.predecessors(node_id):
            source_task = tasks.get(source_node_id, None)
            if source_task is None:
                source_task = self.instantiate_task_static(
                    source_node_id,
                    tasks=tasks,
                    varinfo=varinfo,
                    evict_result_counter=evict_result_counter,
                )
            link_attrs = self.graph[source_node_id][node_id]
            inittask.add_dynamic_inputs(
                dynamic_inputs, link_attrs, source_task.output_variables
            )
            # Evict intermediate results
            if evict_result_counter:
                evict_result_counter[source_node_id] -= 1
                if evict_result_counter[source_node_id] == 0:
                    tasks.pop(source_node_id)
        # Instantiate the requested task
        target_task = self.instantiate_task(
            node_id, varinfo=varinfo, inputs=dynamic_inputs
        )
        tasks[node_id] = target_task
        return target_task

    def successors(self, node_id: NodeIdType, **include_filter):
        yield from self._iter_downstream_nodes(
            node_id, recursive=False, **include_filter
        )

    def descendants(self, node_id: NodeIdType, **include_filter):
        yield from self._iter_downstream_nodes(
            node_id, recursive=True, **include_filter
        )

    def predecessors(self, node_id: NodeIdType, **include_filter):
        yield from self._iter_upstream_nodes(node_id, recursive=False, **include_filter)

    def ancestors(self, node_id: NodeIdType, **include_filter):
        yield from self._iter_upstream_nodes(node_id, recursive=True, **include_filter)

    def has_successors(self, node_id: NodeIdType, **include_filter):
        return self._iterator_has_items(self.successors(node_id, **include_filter))

    def has_descendants(self, node_id: NodeIdType, **include_filter):
        return self._iterator_has_items(self.descendants(node_id, **include_filter))

    def has_predecessors(self, node_id: NodeIdType, **include_filter):
        return self._iterator_has_items(self.predecessors(node_id, **include_filter))

    def has_ancestors(self, node_id: NodeIdType, **include_filter):
        return self._iterator_has_items(self.ancestors(node_id, **include_filter))

    @staticmethod
    def _iterator_has_items(iterator):
        try:
            next(iterator)
            return True
        except StopIteration:
            return False

    def _iter_downstream_nodes(self, node_id: NodeIdType, **kw):
        yield from self._iter_nodes(node_id, upstream=False, **kw)

    def _iter_upstream_nodes(self, node_id: NodeIdType, **kw):
        yield from self._iter_nodes(node_id, upstream=True, **kw)

    def _iter_nodes(
        self,
        node_id: NodeIdType,
        upstream=False,
        recursive=False,
        _visited=None,
        **include_filter,
    ):
        """Recursion is not stopped by the node or link filters.
        Recursion is stopped by either not having any successors/predecessors
        or encountering a node that has been visited already.
        The original node on which we start iterating is never included.
        """
        if recursive:
            if _visited is None:
                _visited = set()
            elif node_id in _visited:
                return
            _visited.add(node_id)
        if upstream:
            iter_next_nodes = self.graph.predecessors
        else:
            iter_next_nodes = self.graph.successors
        for next_id in iter_next_nodes(node_id):
            node_is_included = self._filter_node(next_id, **include_filter)
            if upstream:
                link_is_included = self._filter_link(next_id, node_id, **include_filter)
            else:
                link_is_included = self._filter_link(node_id, next_id, **include_filter)
            if node_is_included and link_is_included:
                yield next_id
            if recursive:
                yield from self._iter_nodes(
                    next_id,
                    upstream=upstream,
                    recursive=True,
                    _visited=_visited,
                    **include_filter,
                )

    def _filter_node(
        self,
        node_id: NodeIdType,
        node_filter=None,
        node_has_predecessors=None,
        node_has_successors=None,
        **linkfilter,
    ):
        """Filters are combined with the logical AND"""
        if callable(node_filter):
            if not node_filter(node_id):
                return False
        if node_has_predecessors is not None:
            if self.has_predecessors(node_id) != node_has_predecessors:
                return False
        if node_has_successors is not None:
            if self.has_successors(node_id) != node_has_successors:
                return False
        return True

    def _filter_link(
        self,
        source_id: NodeIdType,
        target_id: NodeIdType,
        link_filter=None,
        link_has_on_error=None,
        link_has_conditions=None,
        link_is_conditional=None,
        link_has_required=None,
        **nodefilter,
    ):
        """Filters are combined with the logical AND"""
        if callable(link_filter):
            if not link_filter(source_id, target_id):
                return False
        if link_has_on_error is not None:
            if self._link_has_on_error(source_id, target_id) != link_has_on_error:
                return False
        if link_has_conditions is not None:
            if self._link_has_conditions(source_id, target_id) != link_has_conditions:
                return False
        if link_is_conditional is not None:
            if self._link_is_conditional(source_id, target_id) != link_is_conditional:
                return False
        if link_has_required is not None:
            if self._link_has_required(source_id, target_id) != link_has_required:
                return False
        return True

    def _link_has_conditions(self, source_id: NodeIdType, target_id: NodeIdType):
        link_attrs = self.graph[source_id][target_id]
        return bool(link_attrs.get("conditions", False))

    def _link_has_on_error(self, source_id: NodeIdType, target_id: NodeIdType):
        link_attrs = self.graph[source_id][target_id]
        return bool(link_attrs.get("on_error", False))

    def _link_has_required(self, source_id: NodeIdType, target_id: NodeIdType):
        link_attrs = self.graph[source_id][target_id]
        return bool(link_attrs.get("required", False))

    def _link_is_conditional(self, source_id: NodeIdType, target_id: NodeIdType):
        link_attrs = self.graph[source_id][target_id]
        return bool(
            link_attrs.get("on_error", False) or link_attrs.get("conditions", False)
        )

    def link_is_required(self, source_id: NodeIdType, target_id: NodeIdType):
        if self._link_has_required(source_id, target_id):
            return True
        if self._link_is_conditional(source_id, target_id):
            return False
        return self._node_is_required(source_id)

    def _node_is_required(self, node_id: NodeIdType):
        return not self.has_ancestors(
            node_id, link_has_required=False, link_is_conditional=True
        )

    def _required_predecessors(self, target_id: NodeIdType):
        for source_id in self.predecessors(target_id):
            if self.link_is_required(source_id, target_id):
                yield source_id

    def _has_required_predecessors(self, node_id: NodeIdType):
        return self._iterator_has_items(self._required_predecessors(node_id))

    def _has_required_static_inputs(self, node_id: NodeIdType):
        """Returns True when the default inputs cover all required inputs."""
        node_attrs = self.graph.nodes[node_id]
        inputs_complete = node_attrs.get("inputs_complete", None)
        if isinstance(inputs_complete, bool):
            # method and script tasks always have an empty `required_input_names`
            # although they may have required input. This keyword is used the
            # manually indicate that all required inputs are statically provided.
            return inputs_complete
        taskclass = inittask.get_task_class(node_attrs, node_id=node_id)
        static_inputs = {d["name"] for d in node_attrs.get("default_inputs", list())}
        return not (set(taskclass.required_input_names()) - static_inputs)

    def start_nodes(self) -> Set[NodeIdType]:
        nodes = set(
            node_id
            for node_id in self.graph.nodes
            if not self.has_predecessors(node_id)
        )
        if nodes:
            return nodes
        return set(
            node_id
            for node_id in self.graph.nodes
            if self._has_required_static_inputs(node_id)
            and not self._has_required_predecessors(node_id)
        )

    def end_nodes(self) -> Set[NodeIdType]:
        nodes = set(
            node_id for node_id in self.graph.nodes if not self.has_successors(node_id)
        )
        if nodes:
            return nodes
        return set(
            node_id
            for node_id in self.graph.nodes
            if self._node_has_noncovered_conditions(node_id)
        )

    def _node_has_noncovered_conditions(self, source_id: NodeIdType) -> bool:
        links = self._get_node_expanded_conditions(source_id)
        has_complement = [False] * len(links)

        default_complements = {CONDITIONS_ELSE_VALUE}
        complements = {
            CONDITIONS_ELSE_VALUE: None,
            True: {False, CONDITIONS_ELSE_VALUE},
            False: {True, CONDITIONS_ELSE_VALUE},
        }

        for i, conditions1 in enumerate(links):
            if has_complement[i]:
                continue
            for j in range(i + 1, len(links)):
                conditions2 = links[j]
                if self._conditions_are_complementary(
                    conditions1, conditions2, default_complements, complements
                ):
                    has_complement[i] = True
                    has_complement[j] = True
                    break
            if not has_complement[i]:
                return True
        return False

    @staticmethod
    def _conditions_are_complementary(
        conditions1, conditions2, default_complements, complements
    ):
        for varname, value in conditions1.items():
            complementary_values = complements.get(value, default_complements)
            if complementary_values is None:
                # Any value is complementary
                continue
            if conditions2[varname] not in complementary_values:
                return False
        return True

    def _get_node_expanded_conditions(self, source_id: NodeIdType):
        """Ensure that conditional link starting from a source node has
        the same set of output names.
        """
        links = [
            self.graph[source_id][target_id]["conditions"]
            for target_id in self.successors(source_id, link_has_conditions=True)
        ]
        all_condition_names = {
            item["source_output"] for conditions in links for item in conditions
        }
        for conditions in links:
            link_condition_names = {item["source_output"] for item in conditions}
            for name in all_condition_names - link_condition_names:
                conditions.append(
                    {"source_output": name, "value": CONDITIONS_ELSE_VALUE}
                )
        return links

    def validate_graph(self):
        for node_id, node_attrs in self.graph.nodes.items():
            inittask.validate_task_executable(node_attrs, node_id=node_id)

            # Isolated nodes do no harm so comment this
            # if len(graph.nodes) > 1 and not node_has_links(graph, node_id):
            #    raise ValueError(f"Node {repr(node_id)} has no links")

            inputs_from_required = dict()
            for source_id in self._required_predecessors(node_id):
                link_attrs = self.graph[source_id][node_id]
                arguments = link_attrs.get("data_mapping", list())
                for arg in arguments:
                    try:
                        name = arg["target_input"]
                    except KeyError:
                        raise KeyError(
                            f"Argument '{arg}' of link '{source_id}' -> '{node_id}' is missing an 'input' key"
                        ) from None
                    other_source_id = inputs_from_required.get(name)
                    if other_source_id:
                        raise ValueError(
                            f"Node {repr(source_id)} and {repr(other_source_id)} both connect to the input {repr(name)} of {repr(node_id)}"
                        )
                    inputs_from_required[name] = source_id

        for (source, target), linkattrs in self.graph.edges.items():
            err_msg = (
                f"Link {source}->{target}: '{{}}' and '{{}}' cannot be used together"
            )
            if linkattrs.get("map_all_data") and linkattrs.get("data_mapping"):
                raise ValueError(err_msg.format("map_all_data", "data_mapping"))
            if linkattrs.get("on_error") and linkattrs.get("conditions"):
                raise ValueError(err_msg.format("on_error", "conditions"))

    def update_default_inputs(self, default_inputs: List[dict]):
        """Input items have the following keys:
        * id: node id
        * label (optional): used when id is missing
        * name: input variable name
        * value: input variable value
        * all (optional): used when id and label is missing (True: all nodes, False: start nodes)
        """
        self.parse_default_inputs(default_inputs)
        for input_item in default_inputs:
            node_id = input_item.get("id")
            if node_id is None:
                continue
            node_attrs = self.graph.nodes[node_id]
            existing_inputs = node_attrs.get("default_inputs")
            if existing_inputs:
                for existing_input_item in existing_inputs:
                    if existing_input_item["name"] == input_item["name"]:
                        existing_input_item["value"] = input_item["value"]
                        break
                else:
                    existing_inputs.append(input_item)
            else:
                node_attrs["default_inputs"] = [input_item]

    def parse_default_inputs(self, default_inputs: List[dict]):
        extra = list()
        required = {"name", "value"}
        for input_item in default_inputs:
            missing = required - input_item.keys()
            if missing:
                raise ValueError(f"missing keys in one of the graph inputs: {missing}")
            if "id" in input_item:
                continue
            elif "label" in input_item:
                node_label = input_item["label"]
                node_id = self.get_node_id(node_label)
                if node_id is None:
                    raise ValueError(f"Node label '{node_label}' does not exist")
                input_item["id"] = node_id
            else:
                if input_item.get("all"):
                    nodes = self.graph.nodes
                else:
                    nodes = self.start_nodes()
                for node_id in nodes:
                    input_item = dict(input_item)
                    input_item["id"] = node_id
                    extra.append(input_item)
        default_inputs += extra

    def extract_output_values(
        self, node_id: NodeIdType, task: Task, outputs: List[dict]
    ) -> dict:
        """Output items have the following keys:
        * id: node id
        * label (optional): used when id is missing
        * name (optional): output variable name (all outputs when missing)
        * new_name (optional): optional renaming when name is defined
        * all (optional): used when id and label is missing (True: all nodes, False: end nodes)
        """
        output_values = dict()
        task_output_values = None
        for output_item in outputs:
            if output_item.get("id") != node_id:
                continue
            if task_output_values is None:
                task_output_values = task.output_values
            name = output_item.get("name")
            if name:
                new_name = output_item.get("new_name", name)
                output_values[new_name] = task_output_values.get(
                    name, hashing.UniversalHashable.MISSING_DATA
                )
            else:
                output_values.update(task_output_values)
        return output_values

    def parse_outputs(self, outputs: List[dict]):
        extra = list()
        for output_item in outputs:
            if "id" in output_item:
                continue
            elif "label" in output_item:
                node_label = output_item["label"]
                node_id = self.get_node_id(node_label)
                if node_id is None:
                    raise ValueError(f"Node label '{node_label}' does not exist")
                output_item["id"] = node_id
            else:
                if output_item.get("all"):
                    nodes = self.graph.nodes
                else:
                    nodes = self.end_nodes()
                for node_id in nodes:
                    output_item = dict(output_item)
                    output_item["id"] = node_id
                    extra.append(output_item)
        outputs += extra

    def get_node_id(self, label: str) -> Optional[NodeIdType]:
        for node_id, node_attrs in self.graph.nodes.items():
            node_label = get_node_label(node_attrs, node_id=node_id)
            if label == node_label:
                return node_id

    def topological_sort(self) -> Iterable[NodeIdType]:
        """Sort node names for sequential instantiation+execution of DAGs"""
        if self.is_cyclic:
            raise RuntimeError("Sorting nodes is not possible for cyclic graphs")
        yield from networkx.topological_sort(self.graph)

    def successor_counter(self) -> Dict[NodeIdType, int]:
        nsuccessor = Counter()
        for edge in self.graph.edges:
            nsuccessor[edge[0]] += 1
        return nsuccessor

    def execute(
        self,
        varinfo: Optional[dict] = None,
        raise_on_error: Optional[bool] = True,
        results_of_all_nodes: Optional[bool] = False,
        outputs: Optional[List[dict]] = None,
    ) -> Union[Dict[NodeIdType, Task], Dict[str, Any]]:
        """Sequential execution of DAGs. Returns either
        * all tasks (results_of_all_nodes=True, outputs=None)
        * end tasks (results_of_all_nodes=False, outputs=None)
        * merged dictionary of selected outputs from selected nodes (outputs=[...])
        """
        if self.is_cyclic:
            raise RuntimeError("Cannot execute cyclic graphs")
        if self.has_conditional_links:
            raise RuntimeError("Cannot execute graphs with conditional links")

        # Pepare containers for local state
        if outputs:
            results_of_all_nodes = False
            self.parse_outputs(outputs)
            output_values = dict()
        else:
            output_values = None
        if results_of_all_nodes:
            evict_result_counter = None
        else:
            evict_result_counter = self.successor_counter()
        tasks = dict()

        cleanup_references = not results_of_all_nodes
        for node_id in self.topological_sort():
            task = self.instantiate_task_static(
                node_id,
                tasks=tasks,
                varinfo=varinfo,
                evict_result_counter=evict_result_counter,
            )
            task.execute(
                raise_on_error=raise_on_error, cleanup_references=cleanup_references
            )
            if outputs:
                output_values.update(self.extract_output_values(node_id, task, outputs))
        if outputs:
            return output_values
        else:
            return tasks
