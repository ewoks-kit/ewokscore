from typing import Callable, Optional
import networkx
from packaging.version import parse as parse_version
import logging
import importlib

# Major version: increment when changing the existing schema
# Minor version: increment when adding features or deprecating the existing schema
DEFAULT_VERSION = parse_version("1.0")
LATEST_VERSION = parse_version("1.0")

# Map graph versions to ewokscore version bounds. Whenever we change the schema
# which the current ewokscore version needs and updating is not possible:
#   - increment the ewokscore version
#   - use that version as upper bound of the last item of _VERSION_BOUNDS
#   - use that version as lower bound of a new item of _VERSION_BOUNDS
_VERSION_BOUNDS = None


def get_version_bounds() -> dict:
    global _VERSION_BOUNDS
    if _VERSION_BOUNDS:
        return _VERSION_BOUNDS

    _VERSION_BOUNDS = dict()
    _VERSION_BOUNDS[parse_version("0.0")] = parse_version("0.0"), parse_version("0.0.1")
    _VERSION_BOUNDS[parse_version("0.1")] = parse_version("0.1.0-rc"), None
    _VERSION_BOUNDS[parse_version("0.2")] = parse_version("0.1.0-rc"), None
    _VERSION_BOUNDS[parse_version("1.0")] = parse_version("0.1.0-rc"), None
    return _VERSION_BOUNDS


logger = logging.getLogger(__name__)


def update_graph(graph: networkx.DiGraph) -> bool:
    """Updates the graph to a higher version (returns `True`) or raises an
    exception. If the version is know it wil provide library version bounds
    in the exception message. Returns `False` when the graph does not need
    any update.
    """
    version = graph.graph.get("version", None)
    if version is None:
        version = DEFAULT_VERSION
        graph.graph["version"] = str(version)
        logger.warning(f'Graph is not versioned: assume version "{version}"')
    else:
        version = parse_version(version)
    if version == LATEST_VERSION:
        return False

    update_method = _get_update_method(version)
    if update_method:
        before = graph.graph.get("version", None)
        try:
            update_method(graph)
        except Exception:
            pass  # version is not longer supported
        else:
            after = graph.graph.get("version", None)
            assert before != after, "graph conversion did not update the version"
            return True

    lbound, ubound = get_version_bounds().get(version, (None, None))
    if lbound and ubound:
        raise ValueError(
            f'Graph version "{version}" requires another library version: python -m pip install "ewokscore>={lbound},<{ubound}"`'
        )
    elif lbound:
        raise ValueError(
            f'Graph version "{version}" requires another library version: python -m pip install "ewokscore>={lbound}"'
        )
    elif ubound:
        raise ValueError(
            f'Graph version "{version}" requires another library version: python -m pip install "ewokscore<{ubound}"'
        )
    else:
        raise ValueError(
            f'Graph version "{version}" is either invalid or requires a newer library version: python -m pip install --upgrade ewokscore'
        )


def _get_update_method(version) -> Optional[Callable[[networkx.DiGraph], None]]:
    try:
        mod = importlib.import_module(__name__ + ".v" + str(version).replace(".", "_"))
    except ImportError:
        return None
    return mod.update_graph
