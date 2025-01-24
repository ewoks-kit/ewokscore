# CHANGELOG.md

## Unreleased

New features:

- Support for Python 3.13.

## 1.0.0

Breaking changes:

- Remove deprecated `binding` argument from `execute_graph`.

Bug fixes:

- Fix bug in notebook task instantiation.

## 0.15.0

Breaking changes:

- By default, `discover_tasks_from_modules` now discovers tasks of type `class`, `ppfmethod` and `method` instead of only `class`.

New features:

- `discover_all_tasks` now accepts a `task_type` argument to only discover a specific task type. By default, it discovers tasks of type `class`, `ppfmethod` and `method`, as previously.

## 0.14.0

New features:

- Add `task_options` to `execute_graph` and `instantiate_task`. Currently includes only `profile_directory` to enable task time profiling.

## 0.13.1

- Fix wrong task type when discovering `ppfmethod` tasks

## 0.13.0

- Remove upper bound on `numpy`

## 0.12.0

- Python 3.12.5+: accommodate for `urllib` change of relative paths.

## 0.11.0

- Add support for latest `networkx` version (>="3.4rc0")

## 0.10.0

New features:

- New optional field `requirements` in the `graph` field of the graph schema. This field contain a list of projects that should be present in the Python environment for the graph to be executed.

## 0.9.0

Changes:

- Script tasks: use "-" for single-character and "--" for multi-character script parameter names
- The EWOKS events are send to EWOKS event handlers and to a normal application logger

New features:

- Script tasks: support positional arguments

## 0.8.1

New features:

- `load_graph` is now able to load non-JSON files from a path without extension
- `load_graph` and `convert_graph` accept now `Path` type args for the workflow path and the root directory
- New method `cancel` in `Task` to be called when the task must be cancelled. It is up to each `Task` to implement this method.
- New field `force_start_node` for graph nodes. Setting this field to `True` forcefully marks the node as a start node (i.e. a node that must be executed before others).

Deprecations:

- `ewokscore.graph.serialize`: `ewoks_jsonload_hook` is deprecated. Use `json_load` instead.

## 0.8.0

Do not use.

## 0.7.4

Bug fixes:

- the pyyaml 6.0.2rc1 package is broken for python 3.7 or lower

## 0.7.3

Changes:

- numpy 2.0 is not supported

## 0.7.2

Changes:

- replace deprecated pkg_resources

## 0.7.1

Changes:

- make notebook test flaky for python 3.7

## 0.7.0

New features:

- add support for jupyter notebooks as workflow tasks

## 0.6.1

Changes:

- executable scripts absolute path before execution

## 0.6.0

Changes:

- support executable scripts on linux (scripts that have a shebang)

## 0.5.3

Changes:

- modify task doc strings

## 0.5.2

Changes:

- remove print statement from the task_discovery module

## 0.5.1

Changes:

- By default, task discovery raises import errors when modules are specified and
  logs import errors when importing all tasks

## 0.5.0

New features:

- Task discovery without the need to specify modules (using package entry points)

## 0.4.3

New features:

- Module can optionally be reloaded when discovering tasks

## 0.4.2

New features:

- Module can optionally be reloaded when discovering tasks

## 0.4.1

Deprecations:

- Task properties that instantiate objects whenever used are replaced by functions

## 0.4.0

New features:

- CLI support inputs by label or task identifier

Breaking changes:

- CLI option "--output" renamed to "--outputs"

## 0.3.3

Changes:

- tasks discovery includes the current working directory

## 0.3.2

Changes:

- make discover_tasks_from_modules pickelable

## 0.3.1

Deprecations:

- ewoks event field "binding" is deprecated in favor of "engine"

## 0.3.0

Breaking changes:

- `Variable` methods `variable_values`, `named_variable_values`, `positional_variable_values`
  no longer values of type `MissingData`.

## 0.2.1

Bug fixes:

- Store only "name" and "value" of dynamic inputs in node default inputs

## 0.2.0

New features:

- Workflow inputs and outputs: use `task_identifier` to select nodes

## 0.1.1

Bug fixes:

- Add missing `packaging` dependency

## 0.1.0

New features:

- `Graph` class as an API for all task graphs
- `Task` class as an API for all tasks
- `Variable` class for task parameters, hashing and
  persistence (JSON, HDF5-Nexus)
- `load_graph` for loading graph from JSON or YAML
- `execute_graph` for naive task scheduling in a single thread
- Execution events based on python's logging facility
