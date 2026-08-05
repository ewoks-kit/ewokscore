import networkx


class _FrozenDict(dict):
    """A `dict` that raises on any attempt to mutate it in place, except for
    setting keys listed in `_mutable_keys`.

    A `dict` subclass rather than a `MappingProxyType` so it keeps passing
    `isinstance(..., dict)` checks (e.g. in `networkx` and in the ewoks
    serializers), which treat it as a regular, copyable dict.
    """

    _mutable_keys: frozenset = frozenset()

    def __reduce__(self):
        # Pickle's default dict-subclass reduction reconstructs via
        # `cls.__new__(cls)` followed by per-item `__setitem__` calls,
        # which `_read_only` rejects. Reconstruct through the constructor
        # instead, which populates the dict without going through
        # `__setitem__`.
        return (self.__class__, (dict(self),))

    def __setitem__(self, key, value) -> None:
        if key not in self._mutable_keys:
            self._read_only()
        dict.__setitem__(self, key, value)

    def _read_only(self, *args, **kwargs) -> None:
        raise TypeError("This graph, node or link attribute dict is read-only")

    __delitem__ = _read_only
    clear = _read_only
    pop = _read_only
    popitem = _read_only
    setdefault = _read_only
    update = _read_only


class _NodeAttrs(_FrozenDict):
    """Node attributes are frozen except for `default_inputs`."""

    _mutable_keys = frozenset({"default_inputs"})


class FrozenDiGraph(networkx.DiGraph):
    """A `networkx.DiGraph` copy constructor whose node, link and graph
    attribute dicts are read-only, except for a node's `default_inputs`.
    """

    def __init__(self, incoming_graph_data=None, **attr) -> None:
        super().__init__(incoming_graph_data, **attr)
        if incoming_graph_data is None:
            return

        self.graph = _FrozenDict(self.graph)
        for node_id, node_attrs in list(self.nodes(data=True)):
            self._node[node_id] = _NodeAttrs(node_attrs)
        for source_id, target_id, link_attrs in list(self.edges(data=True)):
            frozen_attrs = _FrozenDict(link_attrs)
            self._succ[source_id][target_id] = frozen_attrs
            self._pred[target_id][source_id] = frozen_attrs

        networkx.freeze(self)

    def __setattr__(self, name: str, value) -> None:
        if name == "graph" and isinstance(self.__dict__.get("graph"), _FrozenDict):
            raise TypeError("This graph is frozen: 'graph' cannot be reassigned")
        super().__setattr__(name, value)
