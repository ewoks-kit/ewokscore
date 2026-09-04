from collections import defaultdict
from collections import deque
from functools import cached_property
from typing import Dict
from typing import FrozenSet
from typing import Iterator
from typing import List
from typing import Mapping
from typing import Set

import networkx

from ..inittask import get_task_class
from ..node import NodeIdType
from ._freeze import FrozenDiGraph

# Node -> neighbour -> link attributes
AdjacencyType = Mapping[NodeIdType, Mapping[NodeIdType, dict]]


def _link_is_conditional(link_attrs: dict) -> bool:
    """Whether the link is only triggered for certain results of its source."""
    return bool(link_attrs.get("conditions", False)) or bool(
        link_attrs.get("on_error", False)
    )


def _link_is_locally_optional(link_attrs: dict) -> bool:
    """Whether the link is optional, ignoring everything upstream of its source."""
    required = link_attrs.get("required", None)
    if required is True:
        return False
    if required is False:
        return True
    return _link_is_conditional(link_attrs)


class GraphAnalysis:
    """Graph analysis which derives whole-graph properties at most once.

    Freezes a copy of `graph` on construction, so the original stays mutable
    but the copy used for analysis cannot go stale.

    * Properties of a single node or link are read straight from the graph. They
      cost a dictionary lookup, so caching them would not pay for itself.
    * Properties that need a pass over the whole graph are derived at most once.
    """

    def __init__(self, graph: networkx.DiGraph) -> None:
        self._graph = FrozenDiGraph(graph)
        # Per-node results that are too expensive to re-derive on every call.
        self._descendants: Dict[NodeIdType, FrozenSet[NodeIdType]] = dict()
        self._ancestors: Dict[NodeIdType, FrozenSet[NodeIdType]] = dict()
        self._static_inputs: Dict[NodeIdType, bool] = dict()

    @property
    def graph(self) -> FrozenDiGraph:
        return self._graph

    @property
    def _successors(self) -> AdjacencyType:
        """Node -> successor -> link attributes."""
        return self._graph.succ

    @property
    def _predecessors(self) -> AdjacencyType:
        """Node -> predecessor -> link attributes."""
        return self._graph.pred

    def _link_attrs(self, source_id: NodeIdType, target_id: NodeIdType) -> dict:
        """Attributes of a single link."""
        return self._graph.succ[source_id][target_id]

    # --- Graph properties ---

    def graph_is_cyclic(self) -> bool:
        return self._is_cyclic

    def graph_has_conditional_links(self) -> bool:
        return self._has_conditional_links

    def topological_sort(self) -> Iterator[NodeIdType]:
        """Sort node names for sequential instantiation+execution of DAGs"""
        yield from self._topological_order

    @cached_property
    def _is_cyclic(self) -> bool:
        """Whether the graph contains at least one cycle."""
        return not networkx.is_directed_acyclic_graph(self._graph)

    @cached_property
    def _has_conditional_links(self) -> bool:
        """Whether at least one link is conditional."""
        return any(map(_link_is_conditional, self._graph.edges.values()))

    @cached_property
    def _topological_order(self) -> List[NodeIdType]:
        """All nodes, sources before targets."""
        if self.graph_is_cyclic():
            raise RuntimeError("Sorting nodes is not possible for cyclic graphs")
        return list(networkx.topological_sort(self._graph))

    # --- Link properties ---

    def link_has_conditions(self, source_id: NodeIdType, target_id: NodeIdType) -> bool:
        return bool(self._link_attrs(source_id, target_id).get("conditions", False))

    def link_has_on_error(self, source_id: NodeIdType, target_id: NodeIdType) -> bool:
        return bool(self._link_attrs(source_id, target_id).get("on_error", False))

    def link_is_explicitly_required(
        self, source_id: NodeIdType, target_id: NodeIdType
    ) -> bool:
        return self._link_attrs(source_id, target_id).get("required", None) is True

    def link_is_explicitly_optional(
        self, source_id: NodeIdType, target_id: NodeIdType
    ) -> bool:
        return self._link_attrs(source_id, target_id).get("required", None) is False

    def link_is_conditional(self, source_id: NodeIdType, target_id: NodeIdType) -> bool:
        return _link_is_conditional(self._link_attrs(source_id, target_id))

    def link_is_required(self, source_id: NodeIdType, target_id: NodeIdType) -> bool:
        """Whether the target cannot be executed before this link is triggered.

        An explicit `required` attribute always wins. Conditional links are
        optional by default. Any other link is required when everything upstream
        of its source is connected through required links.
        """
        link_attrs = self._link_attrs(source_id, target_id)
        required = link_attrs.get("required", None)
        if required is True:
            return True
        if required is False:
            return False
        if _link_is_conditional(link_attrs):
            return False
        return self._all_upstream_required[source_id]

    @cached_property
    def _all_upstream_required(self) -> Dict[NodeIdType, bool]:
        """Node -> whether all incoming links of the node and of all its
        ancestors are required.

        This is the fixed point of

            all_upstream_required[target] = all(
                not locally_optional[source, target] and all_upstream_required[source]
                for source in predecessors(target)
            )

        Put differently: one optional link makes everything downstream of it
        non-required. So rather than walking upstream for every link, mark the
        target of every locally optional link and propagate that downstream. This
        visits every link once and terminates on cyclic graphs.
        """
        all_upstream_required = dict.fromkeys(self._graph, True)
        successors = self._successors

        to_visit = deque()
        for (_, target_id), link_attrs in self._graph.edges.items():
            if _link_is_locally_optional(link_attrs):
                if all_upstream_required[target_id]:
                    all_upstream_required[target_id] = False
                    to_visit.append(target_id)

        while to_visit:
            for target_id in successors[to_visit.popleft()]:
                if all_upstream_required[target_id]:
                    all_upstream_required[target_id] = False
                    to_visit.append(target_id)

        return all_upstream_required

    # --- Node properties ---

    def node_has_error_handlers(self, node_id: NodeIdType) -> bool:
        """Whether the node has at least one error handler."""
        return any(
            link_attrs.get("on_error", False)
            for link_attrs in self._graph.succ[node_id].values()
        )

    def node_is_start_node(self, node_id: NodeIdType) -> bool:
        """Whether graph execution starts at this node."""
        if self._graph.nodes[node_id].get("force_start_node", False):
            return True
        return not self._graph.pred[node_id]

    def node_is_pure_end_node(self, node_id: NodeIdType) -> bool:
        """Node without successors or only error handlers"""
        return all(
            link_attrs.get("on_error", False)
            for link_attrs in self._graph.succ[node_id].values()
        )

    def node_is_end_node(self, node_id: NodeIdType) -> bool:
        """A pure end node or a node with uncovered conditions"""
        if self.node_is_pure_end_node(node_id):
            return True
        return self.node_has_noncovered_conditions(node_id)

    def node_condition_values(self, source_id: NodeIdType) -> Dict[str, set]:
        """Source output name -> all values it is compared against in the
        conditional links of this node.
        """
        condition_values = defaultdict(set)
        for link_attrs in self._graph.succ[source_id].values():
            for condition in link_attrs.get("conditions") or ():
                condition_values[condition["source_output"]].add(condition["value"])
        return condition_values

    def node_has_noncovered_conditions(self, source_id: NodeIdType) -> bool:
        """Whether some condition value has no complementary link, in which case
        graph execution can end at this node.

        A boolean value is covered by its negation or by the `else` value, any
        other value only by the `else` value.
        """
        conditions_else_value = self._graph.nodes[source_id].get(
            "conditions_else_value", None
        )
        complements = {
            True: {False, conditions_else_value},
            False: {True, conditions_else_value},
        }
        for values in self.node_condition_values(source_id).values():
            for value in values:
                covered_by = complements.get(value, {conditions_else_value})
                if not (covered_by & values):
                    return True
        return False

    def has_required_static_inputs(self, node_id: NodeIdType) -> bool:
        """Returns True when the default inputs cover all required inputs."""
        result = self._static_inputs.get(node_id)
        if result is None:
            result = self._derive_required_static_inputs(node_id)
            self._static_inputs[node_id] = result
        return result

    def _derive_required_static_inputs(self, node_id: NodeIdType) -> bool:
        """Compare the default inputs of the node with the required inputs of its
        task. Cached by the caller because it needs to import the task class.
        """
        node_attrs = self._graph.nodes[node_id]
        if node_attrs.get("task_type", None) != "class":
            # Tasks that are not `class` (e.g. `method` and `script`)
            # always have an empty `required_input_names`
            # although they may have required input.
            return False
        taskclass = get_task_class(node_id, node_attrs)
        static_inputs = {d["name"] for d in node_attrs.get("default_inputs", list())}
        return not (set(taskclass.required_input_names()) - static_inputs)

    # --- Neighbours ---

    def node_successors(self, node_id: NodeIdType) -> Iterator[NodeIdType]:
        yield from self._graph.succ[node_id]

    def node_predecessors(self, node_id: NodeIdType) -> Iterator[NodeIdType]:
        yield from self._graph.pred[node_id]

    def node_has_successors(self, node_id: NodeIdType) -> bool:
        return bool(self._graph.succ[node_id])

    def node_has_predecessors(self, node_id: NodeIdType) -> bool:
        return bool(self._graph.pred[node_id])

    def descendants(self, node_id: NodeIdType) -> FrozenSet[NodeIdType]:
        """All nodes reachable by following links downstream, cached per node."""
        result = self._descendants.get(node_id)
        if result is None:
            result = self._reachable(node_id, self._successors)
            self._descendants[node_id] = result
        return result

    def ancestors(self, node_id: NodeIdType) -> FrozenSet[NodeIdType]:
        """All nodes reachable by following links upstream, cached per node."""
        result = self._ancestors.get(node_id)
        if result is None:
            result = self._reachable(node_id, self._predecessors)
            self._ancestors[node_id] = result
        return result

    def node_has_descendants(self, node_id: NodeIdType) -> bool:
        return bool(self._graph.succ[node_id])

    def node_has_ancestors(self, node_id: NodeIdType) -> bool:
        return bool(self._graph.pred[node_id])

    @staticmethod
    def _reachable(
        node_id: NodeIdType, adjacency: AdjacencyType
    ) -> FrozenSet[NodeIdType]:
        """All nodes reachable from `node_id` through `adjacency`.

        `node_id` itself is only included when it is part of a cycle.
        """
        visited: Set[NodeIdType] = set()
        to_visit = [node_id]
        # Iterative so that the depth of the graph is not limited
        # by the Python recursion limit.
        while to_visit:
            for next_id in adjacency[to_visit.pop()]:
                if next_id not in visited:
                    visited.add(next_id)
                    to_visit.append(next_id)
        return frozenset(visited)

    # --- Required predecessors ---

    def required_predecessors(self, target_id: NodeIdType) -> Iterator[NodeIdType]:
        """The predecessors without which the target cannot be executed."""
        for source_id in self._graph.pred[target_id]:
            if self.link_is_required(source_id, target_id):
                yield source_id

    def has_required_predecessors(self, node_id: NodeIdType) -> bool:
        """Whether the node has at least one required predecessor."""
        return any(
            self.link_is_required(source_id, node_id)
            for source_id in self._graph.pred[node_id]
        )

    # --- Start and end nodes ---

    def start_nodes(self) -> FrozenSet[NodeIdType]:
        """Nodes from which the graph execution starts"""
        return self._start_nodes

    def end_nodes(self) -> FrozenSet[NodeIdType]:
        """Nodes at which an graph execution thread may end and
        which result need to be recorded.
        """
        return self._end_nodes

    @cached_property
    def _start_nodes(self) -> FrozenSet[NodeIdType]:
        """The nodes without predecessors. When every node has a predecessor,
        the nodes that can be executed right away instead.
        """
        start_nodes = frozenset(
            node_id for node_id in self._graph if self.node_is_start_node(node_id)
        )
        if start_nodes:
            return start_nodes

        return frozenset(
            node_id
            for node_id in self._graph
            if self.has_required_static_inputs(node_id)
            and not self.has_required_predecessors(node_id)
        )

    @cached_property
    def _end_nodes(self) -> FrozenSet[NodeIdType]:
        """The nodes without successors. When every node has a successor, the
        nodes at which execution can stop instead.
        """
        end_nodes = frozenset(
            node_id for node_id in self._graph if self.node_is_pure_end_node(node_id)
        )
        if end_nodes:
            return end_nodes

        return frozenset(
            node_id for node_id in self._graph if self.node_is_end_node(node_id)
        )

    # --- Pure descendants ---

    def node_pure_descendants(
        self, node_id: NodeIdType, include_node: bool = False
    ) -> Iterator[NodeIdType]:
        """Yields all descendants which do not depend on anything else than `node_id`"""
        if include_node:
            yield node_id

        to_yield = self._pure_descendants(node_id)

        # Yield breadth-first, so the order is deterministic.
        successors = self._successors
        yielded: Set[NodeIdType] = set()
        to_visit = deque([node_id])
        while to_visit:
            for target_id in successors[to_visit.popleft()]:
                if target_id in to_yield and target_id not in yielded:
                    yielded.add(target_id)
                    yield target_id
                    to_visit.append(target_id)

    def _pure_descendants(self, node_id: NodeIdType) -> Set[NodeIdType]:
        """The descendants of `node_id` that nothing outside the branch depends on.

        A descendant belongs to the branch when all of its predecessors belong to
        the branch.
        """
        predecessors = self._predecessors
        successors = self._successors

        # The pure decendants of `node_id` are a subset of all descendant.
        branch = set(self.descendants(node_id))
        branch.add(node_id)

        # Remove the nodes that depend on something outside the branch.
        to_check = deque(branch - {node_id})
        while to_check:
            target_id = to_check.popleft()

            if target_id not in branch:
                continue  # already removed

            if branch.issuperset(predecessors[target_id]):
                continue  # depends on the branch only

            # `target_id` depends on something outside the branch
            branch.discard(target_id)

            # If `target_id` depends on something outside do it successors.
            to_check.extend(
                next_id
                for next_id in successors[target_id]
                if next_id in branch and next_id != node_id
            )

        # Remove the root node
        branch.discard(node_id)

        return branch
