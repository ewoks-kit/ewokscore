Modify the Ewoks schema specification
=====================================

When changing the Ewoks schema specification, a new schema version needs to be added to the dictionary returned by ``get_versions`` in ``src/ewokscore/graph/schema/__init__.py``.

The dictionary contains the schema version metadata (more on this below) indexed by versions in increasing order.

.. code-block:: python

    def get_versions() -> Dict[Version, SchemaMetadata]:
        [...]

        return {
            parse_version("0.0"): SchemaMetadata(("0.0", "0.0.1"), v0_update),
            parse_version("1.0"): SchemaMetadata(("0.1.0-rc", None), from_v1_0_to_v1_1),
            parse_version("1.1"): SchemaMetadata(("0.1.0-rc", None), None),
        }


The latest version is defined by the last entry in the dictionary

Define the new version number
-----------------------------

When adding a new schema version, the schema version must be incremented with respect to the last ``get_versions`` entry depending on the change:

- When adding a **backward-compatible change** (e.g. a new `optional` field), the minor part of the version should be incremented (e.g. go from `1.0` to `1.1`)
- When adding a **breaking change** (e.g. a new `required` field or a change in structure), the major part of the version should be incremented (e.g. go from `1.1` to `2.0`).

Add the new version number
--------------------------

To add a new version, add an entry in the dictionary returned by ``get_versions`` with:

- the version number as the key (stored as `Version`_)
- an instance of ``SchemaMetadata`` as value. 

The ``SchemaMetadata`` creation needs two arguments:

- ``ewokscore`` version bounds (stored as a 2-tuple of `Version`_): the first tuple value is the lowest ``ewokscore`` version that supports this schema, the second is the highest version that supports this schema (put ``None`` if there is no upper bound).
- a function that converts this schema version to the next version. The function can be defined in the ``update`` submodule. If the version is the latest one, put ``None`` since there is no next version.



.. _Version: https://packaging.pypa.io/en/stable/version.html#packaging.version.Version
