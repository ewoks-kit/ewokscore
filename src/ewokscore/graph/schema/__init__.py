import logging
from typing import Dict
from typing import Union

import networkx
from packaging.version import Version
from packaging.version import parse as parse_version

from .metadata import SchemaMetadata
from .update import from_v1_0_to_v1_1
from .update import v0_update

_VERSIONS = None


def get_versions() -> Dict[Version, SchemaMetadata]:
    global _VERSIONS
    if _VERSIONS is not None:
        return _VERSIONS

    _VERSIONS = {
        parse_version("0.0"): SchemaMetadata(("0.0", "0.0.1"), v0_update),
        parse_version("1.0"): SchemaMetadata(("0.1.0-rc", None), from_v1_0_to_v1_1),
        parse_version("1.1"): SchemaMetadata(("0.1.0-rc", None), None),
    }
    return _VERSIONS


# Major version: increment when changing the existing schema
# Minor version: increment when adding features or deprecating the existing schema
LATEST_VERSION = list(get_versions().keys())[-1]

# The default version may be set to something else if we don't want the latest version to be the default
DEFAULT_VERSION = LATEST_VERSION


logger = logging.getLogger(__name__)


def normalize_schema_version(graph: Union[dict, networkx.Graph]):
    if isinstance(graph, dict):
        graph_metadata = graph["graph"]
    else:
        graph_metadata = graph.graph
    schema_version = graph_metadata.get("schema_version", None)
    if schema_version:
        pversion = parse_version(schema_version)
    else:
        logger.info(
            'Graph has no "schema_version": assume version "%s"', DEFAULT_VERSION
        )
        pversion = DEFAULT_VERSION
    if pversion != LATEST_VERSION:
        # This warning is given because an exception may occur before `update_graph_schema`
        # is called due to the different schema version.
        logger.warning(
            'Graph schema version "%s" is not equal to the latest version "%s"',
            pversion,
            LATEST_VERSION,
        )

    graph_metadata["schema_version"] = str(pversion)


def update_graph_schema(graph: networkx.DiGraph):
    """
    Updates the graph description to a higher schema version or raises an
    exception.
    If the schema version is known it will provide library version bounds
    in the exception message.
    """
    schema_version = parse_version(graph.graph["schema_version"])

    schema_metadata = get_versions().get(schema_version)
    update_method = schema_metadata.update_method if schema_metadata else None
    if not update_method:
        raise GraphSchemaError(schema_version)

    before = schema_version
    try:
        update_method(graph)
    except Exception:
        raise GraphSchemaError(schema_version)
    else:
        after = parse_version(graph.graph["schema_version"])
        if before == after:
            raise RuntimeError("graph conversion did not update the schema version")
        if before > after:
            raise RuntimeError("graph conversion did not increment the schema version")


class GraphSchemaError(ValueError):
    def __init__(self, schema_version: Version) -> None:
        version_metadata = get_versions().get(schema_version)

        if not version_metadata:
            return super().__init__(
                f'Graph schema version "{schema_version}" is either invalid or requires a newer library version: python3 -m pip install --upgrade ewokscore'
            )
        lbound, ubound = version_metadata.ewokscore_bounds

        if not ubound:
            return super().__init__(
                f'Graph schema version "{schema_version}" requires another library version: python3 -m pip install "ewokscore>={lbound}"'
            )

        return super().__init__(
            f'Graph schema version "{schema_version}" requires another library version: python3 -m pip install "ewokscore>={lbound},<{ubound}"`'
        )
