from collections import OrderedDict
from collections import defaultdict
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import Set

import networkx

from ..inittask import get_task_class
from ..node import NodeIdType


def graph_is_cyclic(graph: networkx.DiGraph) -> bool:
    return not networkx.is_directed_acyclic_graph(graph)


def graph_has_conditional_links(graph: networkx.DiGraph) -> bool:
    for attrs in graph.edges.values():
        if attrs.get("conditions") or attrs.get("on_error"):
            return True
    return False


def node_successors(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
) -> Iterator[NodeIdType]:
    if include_filter:
        yield from iter_downstream_nodes(
            graph, node_id, recursive=False, **include_filter
        )
    else:
        yield from graph.successors(node_id)


def node_descendants(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
) -> Iterator[NodeIdType]:
    yield from iter_downstream_nodes(graph, node_id, recursive=True, **include_filter)


def node_predecessors(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
) -> Iterator[NodeIdType]:
    if include_filter:
        yield from iter_upstream_nodes(
            graph, node_id, recursive=False, **include_filter
        )
    else:
        yield from graph.predecessors(node_id)


def node_ancestors(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
) -> Iterator[NodeIdType]:
    yield from iter_upstream_nodes(graph, node_id, recursive=True, **include_filter)


def iterator_has_items(iterator):
    try:
        next(iterator)
        return True
    except StopIteration:
        return False


def node_has_successors(graph: networkx.DiGraph, node_id: NodeIdType, **include_filter):
    return iterator_has_items(node_successors(graph, node_id, **include_filter))


def node_has_descendants(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
):
    return iterator_has_items(node_descendants(graph, node_id, **include_filter))


def node_has_predecessors(
    graph: networkx.DiGraph, node_id: NodeIdType, **include_filter
):
    return iterator_has_items(node_predecessors(graph, node_id, **include_filter))


def node_has_ancestors(graph: networkx.DiGraph, node_id: NodeIdType, **include_filter):
    return iterator_has_items(node_ancestors(graph, node_id, **include_filter))


def iter_downstream_nodes(
    graph: networkx.DiGraph, node_id: NodeIdType, **kw
) -> Iterator[NodeIdType]:
    yield from _iter_nodes(graph, node_id, upstream=False, **kw)


def iter_upstream_nodes(
    graph: networkx.DiGraph, node_id: NodeIdType, **kw
) -> Iterator[NodeIdType]:
    yield from _iter_nodes(graph, node_id, upstream=True, **kw)


def _iter_nodes(
    graph: networkx.DiGraph,
    node_id: NodeIdType,
    upstream=False,
    recursive=False,
    _visited=None,
    **include_filter,
) -> Iterator[NodeIdType]:
    """Recursion is not stopped by the node or link filters.
    Recursion is stopped by either not having any successors/predecessors
    or encountering a node that has been visited already.
    The original node on which we start iterating is never yielded.
    """
    if recursive:
        if _visited is None:
            _visited = set()
        elif node_id in _visited:
            return
        _visited.add(node_id)
    if upstream:
        iter_next_nodes = graph.predecessors
    else:
        iter_next_nodes = graph.successors
    if not include_filter.get("parsed"):
        include_filter = {f"_{k}": v for k, v in include_filter.items()}
        include_filter["parsed"] = True
    for next_id in iter_next_nodes(node_id):
        node_is_included = _filter_node(graph, next_id, **include_filter)
        if upstream:
            link_is_included = _filter_link(graph, next_id, node_id, **include_filter)
        else:
            link_is_included = _filter_link(graph, node_id, next_id, **include_filter)
        if node_is_included and link_is_included:
            yield next_id
        if recursive:
            yield from _iter_nodes(
                graph,
                next_id,
                upstream=upstream,
                recursive=True,
                _visited=_visited,
                **include_filter,
            )


def _filter_node(
    graph: networkx.DiGraph,
    node_id: NodeIdType,
    _node_filter=None,
    _node_has_predecessors=None,
    _node_has_successors=None,
    _node_has_error_handlers=None,
    **_,
) -> bool:
    """Filters are combined with the logical AND"""
    if callable(_node_filter):
        if not _node_filter(node_id):
            return False
    if _node_has_predecessors is not None:
        if node_has_predecessors(graph, node_id) != _node_has_predecessors:
            return False
    if _node_has_successors is not None:
        if node_has_successors(graph, node_id) != _node_has_successors:
            return False
    if _node_has_error_handlers is not None:
        if node_has_error_handlers(graph, node_id) != _node_has_error_handlers:
            return False
    return True


def _filter_link(
    graph: networkx.DiGraph,
    source_id: NodeIdType,
    target_id: NodeIdType,
    _link_filter=None,
    _link_has_on_error=None,
    _link_has_conditions=None,
    _link_is_conditional=None,
    _link_is_required=None,
    **_,
) -> bool:
    """Filters are combined with the logical AND"""
    if callable(_link_filter):
        if not _link_filter(source_id, target_id):
            return False
    if _link_has_on_error is not None:
        if link_has_on_error(graph, source_id, target_id) != _link_has_on_error:
            return False
    if _link_has_conditions is not None:
        if link_has_conditions(graph, source_id, target_id) != _link_has_conditions:
            return False
    if _link_is_conditional is not None:
        if link_is_conditional(graph, source_id, target_id) != _link_is_conditional:
            return False
    if _link_is_required is not None:
        if link_is_required(graph, source_id, target_id) != _link_is_required:
            return False
    return True


def link_has_conditions(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    link_attrs = graph[source_id][target_id]
    return bool(link_attrs.get("conditions", False))


def link_has_on_error(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    link_attrs = graph[source_id][target_id]
    return bool(link_attrs.get("on_error", False))


def link_is_explicitly_required(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    link_attrs = graph[source_id][target_id]
    return link_attrs.get("required", None) is True


def link_is_explicitly_optional(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    link_attrs = graph[source_id][target_id]
    return link_attrs.get("required", None) is False


def link_is_conditional(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    link_attrs = graph[source_id][target_id]
    return bool(link_attrs.get("on_error", None)) or bool(
        link_attrs.get("conditions", None)
    )


def link_is_required(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    return _LinkRequirementAnalysis(graph).link_is_required(source_id, target_id)


class _LinkRequirementAnalysis:
    def __init__(self, graph: networkx.DiGraph):
        self.graph = graph
        self._ancestors = OrderedDict()
        self._upstream_optional_links = OrderedDict()
        self._starts = None
        self._dominators = None
        self._dominator_intervals = None

    def link_is_required(
        self, source_id: NodeIdType, target_id: NodeIdType
    ) -> bool:
        graph = self.graph

        # Explicitly required or optional
        if link_is_explicitly_required(graph, source_id, target_id):
            return True
        if link_is_explicitly_optional(graph, source_id, target_id):
            return False

        # By default, conditional links are optional
        if link_is_conditional(graph, source_id, target_id):
            return False

        return not self._target_can_bypass_upstream_optional_links(
            source_id, target_id
        )

    def required_predecessors(self, target_id: NodeIdType) -> Iterator[NodeIdType]:
        for source_id in node_predecessors(self.graph, target_id):
            if self.link_is_required(source_id, target_id):
                yield source_id

    def _target_can_bypass_upstream_optional_links(
        self, source_id: NodeIdType, target_id: NodeIdType
    ) -> bool:
        graph = self.graph
        upstream_nodes, optional_links = self._get_upstream_optional_links(source_id)
        if not optional_links:
            return False

        starts = self._start_nodes()
        if not starts:
            return True  # cannot be determined

        if any(
            not self._edge_dominates_target(link, target_id, starts)
            for link in optional_links
        ):
            return True

        # An on-error handler can reach the merge target even though its path still
        # passes through an upstream conditional link.
        target_ancestors = self._ancestors_of(target_id) | {target_id}
        return any(
            _link_is_intrinsically_optional(graph, error_source, error_target)
            and link_has_on_error(graph, error_source, error_target)
            and error_target not in upstream_nodes
            and error_target in target_ancestors
            for error_source in upstream_nodes
            for error_target in graph.successors(error_source)
        )

    def _get_upstream_optional_links(self, source_id):
        upstream_nodes = self._ancestors_of(source_id) | {source_id}
        optional_links = self._upstream_optional_links.pop(source_id, None)
        if optional_links is None:
            optional_links = [
                (upstream_source_id, upstream_target_id)
                for upstream_target_id in upstream_nodes
                for upstream_source_id in self.graph.predecessors(upstream_target_id)
                if _link_is_intrinsically_optional(
                    self.graph, upstream_source_id, upstream_target_id
                )
            ]
        self._upstream_optional_links[source_id] = optional_links
        if len(self._upstream_optional_links) > 128:
            self._upstream_optional_links.popitem(last=False)
        return upstream_nodes, optional_links

    def _start_nodes(self):
        if self._starts is None:
            self._starts = [
                node_id
                for node_id in self.graph.nodes
                if node_is_start_node(self.graph, node_id)
            ]
        return self._starts

    def _ancestors_of(self, node_id: NodeIdType) -> Set[NodeIdType]:
        ancestors = self._ancestors.pop(node_id, None)
        if ancestors is None:
            ancestors = networkx.ancestors(self.graph, node_id)
        self._ancestors[node_id] = ancestors
        if len(self._ancestors) > 128:
            self._ancestors.popitem(last=False)
        return ancestors

    def _edge_dominates_target(
        self, edge, target_id: NodeIdType, starts: Iterable[NodeIdType]
    ) -> bool:
        if self._dominators is None:
            root = object()
            expanded_graph = networkx.DiGraph()
            expanded_graph.add_node(root)
            for node_id in self.graph.nodes:
                expanded_graph.add_node(node_id)
            for node_id in starts:
                expanded_graph.add_edge(root, node_id)
            self._edge_nodes = dict()
            for source_id, edge_target_id in self.graph.edges:
                edge_node = object()
                self._edge_nodes[(source_id, edge_target_id)] = edge_node
                expanded_graph.add_edge(source_id, edge_node)
                expanded_graph.add_edge(edge_node, edge_target_id)
            self._root = root
            self._dominators = networkx.immediate_dominators(expanded_graph, root)
            dominator_children = defaultdict(list)
            for node_id, dominator_id in self._dominators.items():
                if node_id != root:
                    dominator_children[dominator_id].append(node_id)
            intervals = dict()
            clock = 0
            stack = [(root, False)]
            while stack:
                node_id, exiting = stack.pop()
                if exiting:
                    intervals[node_id] = (intervals[node_id][0], clock)
                    continue
                intervals[node_id] = (clock, None)
                clock += 1
                stack.append((node_id, True))
                stack.extend(
                    (child_id, False)
                    for child_id in reversed(dominator_children[node_id])
                )
            self._dominator_intervals = intervals

        edge_node = self._edge_nodes.get(edge)
        edge_interval = self._dominator_intervals.get(edge_node)
        target_interval = self._dominator_intervals.get(target_id)
        return (
            edge_interval is not None
            and target_interval is not None
            and edge_interval[0] <= target_interval[0] < edge_interval[1]
        )

def _link_is_intrinsically_optional(
    graph: networkx.DiGraph, source_id: NodeIdType, target_id: NodeIdType
) -> bool:
    """Optional regardless of the links upstream."""
    if link_is_explicitly_required(graph, source_id, target_id):
        return False
    if link_is_explicitly_optional(graph, source_id, target_id):
        return True
    return link_is_conditional(graph, source_id, target_id)


def node_has_error_handlers(graph: networkx.DiGraph, node_id: NodeIdType):
    return node_has_successors(graph, node_id, link_has_on_error=True)


def required_predecessors(
    graph: networkx.DiGraph, target_id: NodeIdType
) -> Iterator[NodeIdType]:
    yield from _LinkRequirementAnalysis(graph).required_predecessors(target_id)


def has_required_predecessors(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    return iterator_has_items(required_predecessors(graph, node_id))


def has_required_static_inputs(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    """Returns True when the default inputs cover all required inputs."""
    node_attrs = graph.nodes[node_id]
    if node_attrs.get("task_type", None) != "class":
        # Tasks that are not `class` (e.g. `method` and `script`)
        # always have an empty `required_input_names`
        # although they may have required input.
        return False
    taskclass = get_task_class(node_id, node_attrs)
    static_inputs = {d["name"] for d in node_attrs.get("default_inputs", list())}
    return not (set(taskclass.required_input_names()) - static_inputs)


def node_condition_values(
    graph: networkx.DiGraph, source_id: NodeIdType
) -> Dict[str, set]:
    condition_values = defaultdict(set)
    for target_id in node_successors(graph, source_id, link_has_conditions=True):
        for condition in graph[source_id][target_id]["conditions"]:
            varname = condition["source_output"]
            value = condition["value"]
            condition_values[varname].add(value)
    return condition_values


def node_has_noncovered_conditions(
    graph: networkx.DiGraph, source_id: NodeIdType
) -> bool:
    conditions_else_value = graph.nodes[source_id].get("conditions_else_value", None)
    complements = {
        True: {False, conditions_else_value},
        False: {True, conditions_else_value},
    }
    condition_values = node_condition_values(graph, source_id)
    for values in condition_values.values():
        for value in values:
            cvalue = complements.get(value, conditions_else_value)
            if cvalue not in values:
                return True
    return False


def node_is_start_node(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    node = graph.nodes[node_id]
    if node.get("force_start_node", False):
        return True

    return not node_has_predecessors(graph, node_id)


def start_nodes(graph: networkx.DiGraph) -> Set[NodeIdType]:
    """Nodes from which the graph execution starts"""

    start_nodes: Set[NodeIdType] = set(
        node_id for node_id in graph.nodes if node_is_start_node(graph, node_id)
    )
    if start_nodes:
        return start_nodes

    return set(
        node_id
        for node_id in graph.nodes
        if has_required_static_inputs(graph, node_id)
        and not has_required_predecessors(graph, node_id)
    )


def end_nodes(graph: networkx.DiGraph) -> Set[NodeIdType]:
    """Nodes at which an graph execution thread may end and
    which result need to be recorded.
    """
    nodes = set(
        node_id for node_id in graph.nodes if node_is_pure_end_node(graph, node_id)
    )
    if nodes:
        return nodes
    return set(node_id for node_id in graph.nodes if node_is_end_node(graph, node_id))


def node_is_pure_end_node(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    """Node without successors or only error handlers"""
    return not node_has_successors(graph, node_id, link_has_on_error=False)


def node_is_end_node(graph: networkx.DiGraph, node_id: NodeIdType) -> bool:
    """A pure end node or a node with uncovered conditions"""
    if node_is_pure_end_node(graph, node_id):
        return True
    if node_has_noncovered_conditions(graph, node_id):
        return True
    return False


def topological_sort(graph: networkx.DiGraph) -> Iterator[NodeIdType]:
    """Sort node names for sequential instantiation+execution of DAGs"""
    if graph_is_cyclic(graph):
        raise RuntimeError("Sorting nodes is not possible for cyclic graphs")
    yield from networkx.topological_sort(graph)


def node_pure_descendants(
    graph: networkx.DiGraph, node_id: NodeIdType, include_node: bool = False
) -> Iterator[NodeIdType]:
    """Yields all descendants which do not depend on anything else than `node_id`"""
    if include_node:
        yield node_id
    nodes = {node_id}
    iter_successors = {node_id}
    while iter_successors:
        new_iter_successors = set()
        for node_id in iter_successors:
            for target_id in graph.successors(node_id):
                if target_id in nodes:
                    continue  # loopback
                predecessors = set(graph.predecessors(target_id))
                if predecessors - nodes:
                    continue  # depends on a node outside the branch
                yield target_id
                new_iter_successors.add(target_id)
        iter_successors = new_iter_successors
