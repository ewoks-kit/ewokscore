import os
import enum
import networkx
import json
from collections.abc import Mapping
from . import inittask
from .utils import qualname
from .utils import dict_merge
from .subgraph import extract_subgraphs
from .subgraph import add_subgraph_links
from .node import node_name_from_json

CONDITIONS_ELSE_VALUE = "__other__"


def load_graph(source=None, representation=None, **load_options):
    if isinstance(source, TaskGraph):
        return source
    else:
        return TaskGraph(source=source, representation=representation, **load_options)


def execute_graph(source=None, representation=None, varinfo=None, **load_options):
    graph = load_graph(source=source, representation=representation, **load_options)
    return graph.execute(varinfo=varinfo)


def set_graph_defaults(graph_as_dict):
    graph_as_dict.setdefault("directed", True)
    graph_as_dict.setdefault("nodes", list())
    graph_as_dict.setdefault("links", list())


def node_has_links(graph, node_name):
    try:
        next(graph.successors(node_name))
    except StopIteration:
        try:
            next(graph.predecessors(node_name))
        except StopIteration:
            return False
    return True


def merge_graphs(graphs, name=None, rename_nodes=None, **load_options):
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
    if name:
        ret.graph.graph["name"] = name
    return ret


def flatten_multigraph(graph):
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


def get_subgraphs(graph, **load_options):
    subgraphs = dict()
    for node_name, node_attrs in graph.nodes.items():
        name, value = inittask.task_executable_key(
            node_attrs, node_name=node_name, all=True
        )
        if name == "graph":
            g = load_graph(value, **load_options)
            g.graph.graph["name"] = node_name
            subgraphs[node_name] = g
    return subgraphs


def _ewoks_jsonload_hook_pair(item):
    key, value = item
    if key in ("source", "target"):
        value = node_name_from_json(value)
    return key, value


def ewoks_jsonload_hook(items):
    return dict(map(_ewoks_jsonload_hook_pair, items))


def abs_path(path, root_dir=None):
    if os.path.isabs(path):
        return path
    if root_dir:
        path = os.path.join(root_dir, path)
    return os.path.abspath(path)


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

    GraphRepresentation = enum.Enum(
        "GraphRepresentation", "json_file json_dict json_string yaml"
    )

    def __init__(self, source=None, representation=None, **load_options):
        self.load(source=source, representation=representation, **load_options)

    def __repr__(self):
        return self.graph.graph.get("name", qualname(type(self)))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError(other, type(other))
        return self.dump() == other.dump()

    def load(self, source=None, representation=None, root_dir=None):
        """From persistent to runtime representation"""
        if representation is None:
            if isinstance(source, Mapping):
                representation = self.GraphRepresentation.json_dict
            elif isinstance(source, str):
                if source.endswith(".json"):
                    representation = self.GraphRepresentation.json_file
                else:
                    representation = self.GraphRepresentation.json_string
        if not source:
            graph = networkx.DiGraph()
        elif isinstance(source, networkx.Graph):
            graph = source
        elif isinstance(source, TaskGraph):
            graph = source.graph
        elif representation == self.GraphRepresentation.json_dict:
            set_graph_defaults(source)
            graph = networkx.readwrite.json_graph.node_link_graph(source)
        elif representation == self.GraphRepresentation.json_file:
            source = abs_path(source, root_dir)
            with open(source, mode="r") as f:
                source = json.load(f, object_pairs_hook=ewoks_jsonload_hook)
            set_graph_defaults(source)
            graph = networkx.readwrite.json_graph.node_link_graph(source)
        elif representation == self.GraphRepresentation.json_string:
            source = json.loads(source, object_pairs_hook=ewoks_jsonload_hook)
            set_graph_defaults(source)
            graph = networkx.readwrite.json_graph.node_link_graph(source)
        elif representation == self.GraphRepresentation.yaml:
            source = abs_path(source, root_dir)
            graph = networkx.readwrite.read_yaml(source)
        else:
            raise TypeError(representation, type(representation))

        if not networkx.is_directed(graph):
            raise TypeError(graph, type(graph))

        graph = flatten_multigraph(graph)
        subgraphs = get_subgraphs(graph, root_dir=root_dir)
        if subgraphs:
            # Extract
            edges, update_attrs = extract_subgraphs(graph, subgraphs)

            # Merged
            self.graph = graph
            graphs = [self] + list(subgraphs.values())
            rename_nodes = [False] + [True] * len(subgraphs)
            graph = merge_graphs(
                graphs,
                name=graph.graph.get("name"),
                rename_nodes=rename_nodes,
                root_dir=root_dir,
            ).graph

            # Re-link
            add_subgraph_links(graph, edges, update_attrs)

        self.graph = graph
        self.validate_graph()

    def dump(self, destination=None, representation=None, **kw):
        """From runtime to persistent representation"""
        if representation is None:
            if isinstance(destination, str) and destination.endswith(".json"):
                representation = self.GraphRepresentation.json_file
            else:
                representation = self.GraphRepresentation.json_dict
        if representation == self.GraphRepresentation.json_dict:
            return networkx.readwrite.json_graph.node_link_data(self.graph)
        elif representation == self.GraphRepresentation.json_file:
            dictrepr = self.dump()
            with open(destination, mode="w") as f:
                json.dump(dictrepr, f, **kw)
            return destination
        elif representation == self.GraphRepresentation.json_string:
            dictrepr = self.dump()
            return json.dumps(dictrepr, **kw)
        elif representation == self.GraphRepresentation.yaml:
            return networkx.readwrite.write_yaml(self.graph, destination, **kw)
        else:
            raise TypeError(representation, type(representation))

    def serialize(self):
        return self.dump(representation=self.GraphRepresentation.json_string)

    @property
    def is_cyclic(self):
        return not networkx.is_directed_acyclic_graph(self.graph)

    @property
    def has_conditional_links(self):
        for attrs in self.graph.edges.values():
            if attrs.get("conditions") or attrs.get("on_error"):
                return True
        return False

    def instantiate_task(self, node_name, varinfo=None, inputs=None):
        """Named arguments are dynamic input and Variable config.
        Static input from the persistent representation are
        added internally.

        :param str node_name:
        :param dict or None tasks: keeps upstream tasks
        :param **inputs: dynamic inputs
        :returns Task:
        """
        # Dynamic input has priority over static input
        nodeattrs = self.graph.nodes[node_name]
        return inittask.instantiate_task(
            nodeattrs, node_name=node_name, varinfo=varinfo, inputs=inputs
        )

    def instantiate_task_static(self, node_name, tasks=None, varinfo=None):
        """Instantiate destination task while no access to the dynamic inputs.
        Side effect: `tasks` will contain all predecessors.

        Remark: Only works for DAGs.

        :param str node_name:
        :param dict or None tasks: keeps upstream tasks
        :param dict or None inputs: optional dynamic inputs
        :returns Task:
        """
        if self.is_cyclic:
            raise RuntimeError(f"{self} is cyclic")
        if tasks is None:
            tasks = dict()
        dynamic_inputs = dict()
        for inputnode in self.predecessors(node_name):
            inputtask = tasks.get(inputnode, None)
            if inputtask is None:
                inputtask = self.instantiate_task_static(
                    inputnode, tasks=tasks, varinfo=varinfo
                )
            link_attrs = self.graph[inputnode][node_name]
            inittask.add_dynamic_inputs(
                dynamic_inputs, link_attrs, inputtask.output_variables
            )
        task = self.instantiate_task(node_name, varinfo=varinfo, inputs=dynamic_inputs)
        tasks[node_name] = task
        return task

    def successors(self, node_name, **include_filter):
        yield from self._iter_downstream_nodes(
            node_name, recursive=False, **include_filter
        )

    def descendants(self, node_name, **include_filter):
        yield from self._iter_downstream_nodes(
            node_name, recursive=True, **include_filter
        )

    def predecessors(self, node_name, **include_filter):
        yield from self._iter_upstream_nodes(
            node_name, recursive=False, **include_filter
        )

    def ancestors(self, node_name, **include_filter):
        yield from self._iter_upstream_nodes(
            node_name, recursive=True, **include_filter
        )

    def has_successors(self, node_name, **include_filter):
        return self._iterator_has_items(self.successors(node_name, **include_filter))

    def has_descendants(self, node_name, **include_filter):
        return self._iterator_has_items(self.descendants(node_name, **include_filter))

    def has_predecessors(self, node_name, **include_filter):
        return self._iterator_has_items(self.predecessors(node_name, **include_filter))

    def has_ancestors(self, node_name, **include_filter):
        return self._iterator_has_items(self.ancestors(node_name, **include_filter))

    @staticmethod
    def _iterator_has_items(iterator):
        try:
            next(iterator)
            return True
        except StopIteration:
            return False

    def _iter_downstream_nodes(self, node_name, **kw):
        yield from self._iter_nodes(node_name, upstream=False, **kw)

    def _iter_upstream_nodes(self, node_name, **kw):
        yield from self._iter_nodes(node_name, upstream=True, **kw)

    def _iter_nodes(
        self,
        node_name,
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
            elif node_name in _visited:
                return
            _visited.add(node_name)
        if upstream:
            iter_next_nodes = self.graph.predecessors
        else:
            iter_next_nodes = self.graph.successors
        for next_name in iter_next_nodes(node_name):
            node_is_included = self._filter_node(next_name, **include_filter)
            if upstream:
                link_is_included = self._filter_link(
                    next_name, node_name, **include_filter
                )
            else:
                link_is_included = self._filter_link(
                    node_name, next_name, **include_filter
                )
            if node_is_included and link_is_included:
                yield next_name
            if recursive:
                yield from self._iter_nodes(
                    next_name,
                    upstream=upstream,
                    recursive=True,
                    _visited=_visited,
                    **include_filter,
                )

    def _filter_node(
        self,
        node_name,
        node_filter=None,
        node_has_predecessors=None,
        node_has_successors=None,
        **linkfilter,
    ):
        """Filters are combined with the logical AND"""
        if callable(node_filter):
            if not node_filter(node_name):
                return False
        if node_has_predecessors is not None:
            if self.has_predecessors(node_name) != node_has_predecessors:
                return False
        if node_has_successors is not None:
            if self.has_successors(node_name) != node_has_successors:
                return False
        return True

    def _filter_link(
        self,
        source_name,
        target_name,
        link_filter=None,
        link_has_on_error=None,
        link_has_conditions=None,
        link_is_conditional=None,
        link_has_required=None,
        **nodefilter,
    ):
        """Filters are combined with the logical AND"""
        if callable(link_filter):
            if not link_filter(source_name, target_name):
                return False
        if link_has_on_error is not None:
            if self._link_has_on_error(source_name, target_name) != link_has_on_error:
                return False
        if link_has_conditions is not None:
            if (
                self._link_has_conditions(source_name, target_name)
                != link_has_conditions
            ):
                return False
        if link_is_conditional is not None:
            if (
                self._link_is_conditional(source_name, target_name)
                != link_is_conditional
            ):
                return False
        if link_has_required is not None:
            if self._link_has_required(source_name, target_name) != link_has_required:
                return False
        return True

    def _link_has_conditions(self, source_name, target_name):
        link_attrs = self.graph[source_name][target_name]
        return bool(link_attrs.get("conditions", False))

    def _link_has_on_error(self, source_name, target_name):
        link_attrs = self.graph[source_name][target_name]
        return bool(link_attrs.get("on_error", False))

    def _link_has_required(self, source_name, target_name):
        link_attrs = self.graph[source_name][target_name]
        return bool(link_attrs.get("required", False))

    def _link_is_conditional(self, source_name, target_name):
        link_attrs = self.graph[source_name][target_name]
        return bool(
            link_attrs.get("on_error", False) or link_attrs.get("conditions", False)
        )

    def link_is_required(self, source_name, target_name):
        if self._link_has_required(source_name, target_name):
            return True
        if self._link_is_conditional(source_name, target_name):
            return False
        return self._node_is_required(source_name)

    def _node_is_required(self, node_name):
        return not self.has_ancestors(
            node_name, link_has_required=False, link_is_conditional=True
        )

    def _required_predecessors(self, target_name):
        for source_name in self.predecessors(target_name):
            if self.link_is_required(source_name, target_name):
                yield source_name

    def _has_required_predecessors(self, node_name):
        return self._iterator_has_items(self._required_predecessors(node_name))

    def _has_required_static_inputs(self, node_name):
        """Returns True when the static inputs cover all required inputs."""
        node_attrs = self.graph.nodes[node_name]
        inputs_complete = node_attrs.get("inputs_complete", None)
        if isinstance(inputs_complete, bool):
            # method and script tasks always have an empty `required_input_names`
            # although they may have required input. This keyword is used the
            # manually indicate that all required inputs are statically provided.
            return inputs_complete
        taskclass = inittask.get_task_class(node_attrs, node_name=node_name)
        static_inputs = node_attrs.get("inputs", dict())
        return not (set(taskclass.required_input_names()) - set(static_inputs.keys()))

    def start_nodes(self):
        nodes = set(
            node_name
            for node_name in self.graph.nodes
            if not self.has_predecessors(node_name)
        )
        if nodes:
            return nodes
        return set(
            node_name
            for node_name in self.graph.nodes
            if self._has_required_static_inputs(node_name)
            and not self._has_required_predecessors(node_name)
        )

    def result_nodes(self):
        """The outputs of these nodes are considered to be the "output of the graph" """
        nodes = set(
            node_name
            for node_name in self.graph.nodes
            if not self.has_successors(node_name)
        )
        if nodes:
            return nodes
        return set(
            node_name
            for node_name in self.graph.nodes
            if self._node_has_noncovered_conditions(node_name)
        )

    def _node_has_noncovered_conditions(self, source_name) -> bool:
        links = self._get_node_explanded_conditions(source_name)
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

    def _get_node_explanded_conditions(self, source_name):
        links = [
            self.graph[source_name][target_name]["conditions"]
            for target_name in self.successors(source_name, link_has_conditions=True)
        ]
        all_names = {name for conditions in links for name in conditions}
        for conditions in links:
            for name in all_names:
                conditions.setdefault(name, CONDITIONS_ELSE_VALUE)
        return links

    def validate_graph(self):
        for node_name, node_attrs in self.graph.nodes.items():
            inittask.validate_task_executable(node_attrs, node_name=node_name)

            # Isolated nodes do no harm so comment this
            # if len(graph.nodes) > 1 and not node_has_links(graph, node_name):
            #    raise ValueError(f"Node {repr(node_name)} has no links")

            inputs_from_required = dict()
            for source_name in self._required_predecessors(node_name):
                link_attrs = self.graph[source_name][node_name]
                node_outputs = link_attrs.get("arguments", set())
                for name in node_outputs:
                    other_source_name = inputs_from_required.get(name)
                    if other_source_name:
                        raise ValueError(
                            f"Node {repr(source_name)} and {repr(other_source_name)} both connect to the input {repr(name)} of {repr(node_name)}"
                        )
                    inputs_from_required[name] = source_name

        for (source, target), linkattrs in self.graph.edges.items():
            err_msg = (
                f"Link {source}->{target}: '{{}}' and '{{}}' cannot be used together"
            )
            if linkattrs.get("all_arguments") and linkattrs.get("arguments"):
                raise ValueError(err_msg.format("all_arguments", "arguments"))
            if linkattrs.get("on_error") and linkattrs.get("conditions"):
                raise ValueError(err_msg.format("on_error", "conditions"))

    def topological_sort(self):
        """Sort node names for sequential instantiation+execution of DAGs"""
        if self.is_cyclic:
            raise RuntimeError("Sorting nodes is not possible for cyclic graphs")
        yield from networkx.topological_sort(self.graph)

    def execute(self, varinfo=None):
        """Sequential execution of DAGs"""
        if self.is_cyclic:
            raise RuntimeError("Cannot execute cyclic graphs")
        if self.has_conditional_links:
            raise RuntimeError("Cannot execute graphs with conditional links")
        tasks = dict()
        for node in self.topological_sort():
            task = self.instantiate_task_static(node, tasks=tasks, varinfo=varinfo)
            task.execute()
        return tasks
