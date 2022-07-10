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


def normalize_schema_version(graph: dict):
    schema_version = graph["graph"].get("schema_version", None)
    if not schema_version:
        schema_version = DEFAULT_VERSION
        graph["graph"]["schema_version"] = str(schema_version)
        logger.info(
            'Graph has no "schema_version": assume version "%s"', schema_version
        )
        return
    pversion = parse_version(schema_version)
    if pversion != LATEST_VERSION:
        # This warning is given because an exception may occur before `update_graph_schema`
        # is called due to the different schema version.
        logger.warning(
            'Graph schema version "%s" is not equal to the latest version "%s"',
            pversion,
            LATEST_VERSION,
        )
    graph["graph"]["schema_version"] = str(pversion)


def update_graph_schema(graph: networkx.DiGraph) -> bool:
    """Updates the graph description to a higher schema version (returns `True`) or raises an
    exception. If the schema version is known it will provide library version bounds
    in the exception message. Returns `False` when the graph does not need
    any update.
    """
    schema_version = graph.graph.get("schema_version", None)
    if schema_version is None:
        schema_version = DEFAULT_VERSION
        graph.graph["schema_version"] = str(schema_version)
        logger.info(
            'Graph has no "schema_version": assume version "%s"', schema_version
        )
    else:
        schema_version = parse_version(schema_version)
    if schema_version == LATEST_VERSION:
        return False

    update_method = _get_update_method(schema_version)
    if update_method:
        before = graph.graph.get("schema_version", None)
        try:
            update_method(graph)
        except Exception:
            pass  # version is not longer supported
        else:
            after = graph.graph.get("schema_version", None)
            assert before != after, "graph conversion did not update the schema version"
            return True

    lbound, ubound = get_version_bounds().get(schema_version, (None, None))
    if lbound and ubound:
        raise ValueError(
            f'Graph schema version "{schema_version}" requires another library version: python3 -m pip install "ewokscore>={lbound},<{ubound}"`'
        )
    elif lbound:
        raise ValueError(
            f'Graph schema version "{schema_version}" requires another library version: python3 -m pip install "ewokscore>={lbound}"'
        )
    elif ubound:
        raise ValueError(
            f'Graph schema version "{schema_version}" requires another library version: python3 -m pip install "ewokscore<{ubound}"'
        )
    else:
        raise ValueError(
            f'Graph schema version "{schema_version}" is either invalid or requires a newer library version: python3 -m pip install --upgrade ewokscore'
        )


def _get_update_method(schema_version) -> Optional[Callable[[networkx.DiGraph], None]]:
    try:
        mod = importlib.import_module(
            __name__ + ".v" + str(schema_version).replace(".", "_")
        )
    except ImportError:
        return None
    return mod.update_graph_schema
