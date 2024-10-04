Modify the Ewoks schema specification
=====================================

The latest version of the Ewoks schema specification is held in the `LATEST_VERSION` variable in `src/ewokscore/graph/schema/__init__.py`.

When changing the Ewoks schema specification, this version should be changed depending on the change:
- When adding a backward-compatible change (e.g. a new **optional** field), the minor part of the version should be incremented (e.g. go from `1.0` to `1.1`)
- When adding a breaking change (e.g. a new **required** field or a change in structure), the major part of the version should be incremented (e.g. go from `1.1` to `2.0`).

Then, `ewokscore` version bounds for this schema version should be added: the lowest `ewokscore` version that supports this schema and the highest version that supports this schema.

For this, edit `get_version_bounds` by adding an entry to `_VERSION_BOUNDS`. Change the upper bound of the previous schema if needed.

---

Finally, an update method should be added to convert the previous schema version to the new version. 

For example, say we updated the version to `2.0` from `1.1`. Then, we need to add a Python module called `v1_1` in `src/ewokscore/graph/schema` with a function `update_graph_schema`. This function should take care of converting a graph of schema version `1.1` to a graph of schema version `2.0`. The content of this function depends on the change made to the schema.