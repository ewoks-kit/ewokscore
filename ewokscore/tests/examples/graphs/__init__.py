import pkgutil
import importlib
from functools import wraps

ALL_GRAPHS = None


def _discover_graphs():
    if ALL_GRAPHS is None:
        for pkginfo in pkgutil.walk_packages(__path__, __name__ + "."):
            importlib.import_module(pkginfo.name)


def graph_names():
    _discover_graphs()
    return ALL_GRAPHS.keys()


def get_graph(name) -> tuple:
    _discover_graphs()
    return ALL_GRAPHS[name]


def graph(graph_method):
    global ALL_GRAPHS
    name = graph_method.__name__

    @wraps(graph_method)
    def wrapper():
        g, result = graph_method()
        g.setdefault("graph", dict()).setdefault("id", name)
        g.setdefault("graph", dict()).setdefault("label", name)
        return g, result

    if ALL_GRAPHS is None:
        ALL_GRAPHS = dict()
    ALL_GRAPHS[name] = wrapper()
    return wrapper
