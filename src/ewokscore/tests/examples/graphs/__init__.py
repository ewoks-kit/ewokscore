import importlib
import pkgutil
from copy import deepcopy
from functools import wraps

_ALL_GRAPHS = None


def _discover_graphs():
    if _ALL_GRAPHS is None:
        for pkginfo in pkgutil.walk_packages(__path__, __name__ + "."):
            importlib.import_module(pkginfo.name)


def graph_names():
    _discover_graphs()
    return _ALL_GRAPHS.keys()


def get_graph(name) -> tuple:
    _discover_graphs()
    if name not in _ALL_GRAPHS:
        raise ValueError(f"{name!r} is not a known test graph")
    return deepcopy(_ALL_GRAPHS[name])


def graph(graph_method):
    global _ALL_GRAPHS
    name = graph_method.__name__

    @wraps(graph_method)
    def wrapper():
        g, result = graph_method()
        attrs = g.setdefault("graph", dict())
        assert attrs.get("id") == name
        assert attrs.get("label") == name
        assert attrs.get("schema_version") == "1.1"
        return g, result

    if _ALL_GRAPHS is None:
        _ALL_GRAPHS = dict()
    _ALL_GRAPHS[name] = wrapper()
    return wrapper
