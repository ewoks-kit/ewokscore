from collections import defaultdict
from collections import deque
from functools import cached_property
from typing import Callable
from typing import Dict
from typing import FrozenSet
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Mapping
from typing import Set
from typing import Tuple

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
        optional by default. Any other link is required unless an optional event
        upstream of its source can leave the source unexecuted while the target
        can still be reached from the start nodes.

        An optional event is a locally optional link or the failure of a node with
        error handlers (none of its other links are triggered).
        """
        link_attrs = self._link_attrs(source_id, target_id)
        required = link_attrs.get("required", None)
        if required is True:
            return True
        if required is False:
            return False
        if _link_is_conditional(link_attrs):
            return False
        node_index = self._node_index
        upstream_events = self._upstream_optional_events[node_index[source_id]]
        unavoidable_events = self._unavoidable_optional_events[node_index[target_id]]
        return not (upstream_events & ~unavoidable_events)

    @cached_property
    def _node_index(self) -> Dict[NodeIdType, int]:
        """Node -> its number in `_event_flow_graph`."""
        return {node_id: index for index, node_id in enumerate(self._graph)}

    @cached_property
    def _event_flow_graph(self) -> Tuple[List[List[Tuple[int, int]]], List[int], int]:
        """The graph with the failure event of every node with error handlers
        inserted as a node between the node and the targets of its other links.

        Returns the successors of every node together with the event bit of the
        link (0 when not locally optional), the event bit of every node (0 when
        not a failure event) and the number of events. The nodes of the graph
        come first, numbered as in `_node_index`.
        """
        node_index = self._node_index
        successors: List[List[Tuple[int, int]]] = [[] for _ in node_index]
        node_bits = [0] * len(node_index)
        num_events = 0

        failure_events = dict()
        for node_id, links in self._successors.items():
            if any(link_attrs.get("on_error") for link_attrs in links.values()):
                event = len(successors)
                successors.append([])
                node_bits.append(1 << num_events)
                num_events += 1
                successors[node_index[node_id]].append((event, 0))
                failure_events[node_id] = event

        for (source_id, target_id), link_attrs in self._graph.edges.items():
            if source_id in failure_events and not link_attrs.get("on_error"):
                source = failure_events[source_id]
            else:
                source = node_index[source_id]
            link_bit = 0
            if _link_is_locally_optional(link_attrs):
                link_bit = 1 << num_events
                num_events += 1
            successors[source].append((node_index[target_id], link_bit))

        return successors, node_bits, num_events

    @cached_property
    def _upstream_optional_events(self) -> List[int]:
        """Node number -> mask of the optional events with a link into the node
        or into one of its ancestors.
        """
        successors, node_bits, _ = self._event_flow_graph
        order = _reverse_postorder(successors, range(len(successors)))
        position = [0] * len(successors)
        for index, node in enumerate(order):
            position[node] = index

        # One pass in topological order is enough, except for the links that
        # close a cycle: propagate from their targets again.
        masks = [0] * len(successors)
        to_visit = []
        for node in order:
            mask = masks[node] | node_bits[node]
            for next_node, link_bit in successors[node]:
                next_mask = mask | link_bit
                if next_mask & ~masks[next_node]:
                    masks[next_node] |= next_mask
                    if position[next_node] <= position[node]:
                        to_visit.append(next_node)
        while to_visit:
            node = to_visit.pop()
            mask = masks[node] | node_bits[node]
            for next_node, link_bit in successors[node]:
                next_mask = mask | link_bit
                if next_mask & ~masks[next_node]:
                    masks[next_node] |= next_mask
                    to_visit.append(next_node)
        return masks

    @cached_property
    def _unavoidable_optional_events(self) -> List[int]:
        """Node number -> mask of the optional events without which the node
        cannot be reached from the start nodes. No events when there are no start
        nodes, all events for nodes that cannot be reached at all.

        With all start nodes connected to a common root, a failure event is
        unavoidable for the nodes it dominates and a link event for the nodes
        dominated by a link that dominates its own target.
        """
        successors, node_bits, num_events = self._event_flow_graph
        starts = [
            index
            for node_id, index in self._node_index.items()
            if self.node_is_start_node(node_id)
        ]
        if not starts:
            return [0] * len(successors)

        root = len(successors)
        order = _reverse_postorder(successors, starts)
        predecessors: List[List[Tuple[int, int]]] = [[] for _ in range(root + 1)]
        for node in starts:
            predecessors[node].append((root, 0))
        for node in order:
            for next_node, link_bit in successors[node]:
                predecessors[next_node].append((node, link_bit))

        dominators = _immediate_dominators(
            order, predecessors, root, self.graph_is_cyclic()
        )
        dominates = _dominance_test(order, dominators, root)

        masks = [(1 << num_events) - 1] * (root + 1)
        masks[root] = 0
        for node in order:
            dominator = dominators[node]
            mask = masks[dominator] | node_bits[node]
            for predecessor, link_bit in predecessors[node]:
                # A link dominates its target when all other links into the
                # target come from nodes dominated by the target (cycles).
                if (
                    link_bit
                    and predecessor == dominator
                    and all(
                        other == dominator or dominates(node, other)
                        for other, _ in predecessors[node]
                    )
                ):
                    mask |= link_bit
            masks[node] = mask
        return masks

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


def _reverse_postorder(
    successors: List[List[Tuple[int, int]]], roots: Iterable[int]
) -> List[int]:
    """All nodes reachable from the roots, each one before its successors except
    for links closing a cycle.
    """
    visited = [False] * len(successors)
    postorder = []
    for root in roots:
        if visited[root]:
            continue
        visited[root] = True
        stack = [(root, iter(successors[root]))]
        while stack:
            node, next_links = stack[-1]
            for next_node, _ in next_links:
                if not visited[next_node]:
                    visited[next_node] = True
                    stack.append((next_node, iter(successors[next_node])))
                    break
            else:
                stack.pop()
                postorder.append(node)
    postorder.reverse()
    return postorder


def _immediate_dominators(
    order: List[int],
    predecessors: List[List[Tuple[int, int]]],
    root: int,
    cyclic: bool,
) -> List[int]:
    """Node number -> immediate dominator (-1 when not reachable), for nodes in
    reverse postorder from the root (Cooper, Harvey and Kennedy, "A Simple, Fast
    Dominance Algorithm"). One pass suffices for acyclic graphs.
    """
    position = [0] * (root + 1)
    for index, node in enumerate(order, 1):
        position[node] = index
    dominators = [-1] * (root + 1)
    dominators[root] = root
    changed = True
    while changed:
        changed = False
        for node in order:
            new_dominator = -1
            for predecessor, _ in predecessors[node]:
                if dominators[predecessor] == -1:
                    continue
                if new_dominator == -1:
                    new_dominator = predecessor
                    continue
                # Walk up the dominator tree until both paths meet
                a, b = predecessor, new_dominator
                while a != b:
                    while position[a] > position[b]:
                        a = dominators[a]
                    while position[b] > position[a]:
                        b = dominators[b]
                new_dominator = a
            if dominators[node] != new_dominator:
                dominators[node] = new_dominator
                changed = cyclic
    return dominators


def _dominance_test(
    order: List[int], dominators: List[int], root: int
) -> Callable[[int, int], bool]:
    """Returns a function which tells whether a node dominates another one, by
    numbering the dominator tree depth-first.
    """
    children: List[List[int]] = [[] for _ in range(root + 1)]
    for node in order:
        children[dominators[node]].append(node)

    enter = [0] * (root + 1)
    leave = [0] * (root + 1)
    counter = 0
    stack = [(root, iter(children[root]))]
    while stack:
        node, child_nodes = stack[-1]
        child = next(child_nodes, -1)
        counter += 1
        if child == -1:
            stack.pop()
            leave[node] = counter
        else:
            enter[child] = counter
            stack.append((child, iter(children[child])))

    def dominates(node: int, other: int) -> bool:
        return enter[node] <= enter[other] and leave[other] <= leave[node]

    return dominates
