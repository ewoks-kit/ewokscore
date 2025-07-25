# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2025-07-25

### Added

- Ewoks workflow entry interfaces `WorkflowEngine` and `WorkflowEngineWithSerialization`.
- Implement the `WorkflowEngineWithSerialization` interface.
- Add an entry point to the group `ewoks.engines`.
- Add an entry point to the group `ewoks.engines.serialization.representations`.

### Fixed

- Fields of task input models are no longer serialized when executing the task.
  For example, a `dataclass` stays a `dataclass` instead of becoming a `dict`.

## [1.6.0] - 2025-06-10

### Added

- `ewoks.graph.inputs.graph_inputs`: retrieve all "free" inputs parameters of a workflow
  (i.e. not connected to the output of a previous node).
- `ewoks.graph.inputs.graph_inputs_as_table`: same as `graph_inputs` but the result is provided
  in table form suitable for printing in a terminal.

## [1.5.0] - 2025-05-16

### Changed

- Improve `TaskInputError` to describe which task raises the error.
- Improve `RuntimeError` on task failure to describe which task raises the error.
- `BaseInputModel` validation during task execution instead of task construction.

### Fixed

- Apply `BaseInputModel` on the input values when passed with a wrapper (e.g. `Variable`).

## [1.4.0] - 2025-04-23

### Added

- The base Pydantic model `BaseInputModel` now supports fields to accept values of type
  `Variable`, `UniversalHash`, `HasUhash`, `DataProxy`, or `DataUri`. When any of these special
  types are used as input, strict validation is bypassed to allow for deferred evaluation
  when needed.

## [1.3.0] - 2025-04-04

### Added

- Task inputs can now defined via a Pydantic model (`input_model`) instead of `input_names`, `optional_input_names`.
  These two ways of defining inputs are incompatible: one must be used or the other but never simultaneously (including when subclassing tasks).
- Task discovery results now include a `input_model` field. This field is the full qualified name of the model if
  an input model was set for the task, `None` otherwise.

### Deprecated

- `ewokscore.task.Task`: `npositional_inputs` is deprecated in favor of `n_positional_inputs`.

### Fixed

- `convert_graph` no longer adds `directed` and `multigraph` fields. These are not part of the Ewoks specification.
- Hidden and unregistered `class` tasks are no longer included when running task discovery.
- Fix missing `n_required_positional_inputs` field in task discovery results.

## [1.2.0] - 2025-02-11

### Added

- Module patterns can be used as argument of `discover_tasks_from_modules`.

### Fixed

- Fix random order in `required_input_names`, `optional_input_names` and `output_names` fields of discovered tasks of `class` type.

## [1.1.0] - 2025-01-25

### Added

- Support for Python 3.13.

### Changed

- Drop support for Python 3.6 and 3.7.

## [1.0.0] - 2024-12-24

### Changed

- Remove deprecated `binding` argument from `execute_graph`.

### Fixed

- Fix bug in notebook task instantiation.

## [0.15.0] - 2024-11-28

### Added

- `discover_all_tasks` now accepts a `task_type` argument to only discover a specific task type. By default,
  it discovers tasks of type `class`, `ppfmethod` and `method`, as previously.

### Changed

- By default, `discover_tasks_from_modules` now discovers tasks of type `class`, `ppfmethod` and `method` instead of only `class`.

## [0.14.0] - 2024-11-06

### Added

- Add `task_options` to `execute_graph` and `instantiate_task`. Currently includes only `profile_directory` to enable task time profiling.

## [0.13.1] - 2024-10-23

### Fixed

- Fix wrong task type when discovering `ppfmethod` tasks.

## [0.13.0] - 2024-10-16

### Fixed

- Remove upper bound on `numpy`.

## [0.12.0] - 2024-10-15

### Fixed

- Python 3.12.5+: accommodate for `urllib` change of relative paths.

## [0.11.0] - 2024-10-07

### Fixed

- Add support for latest `networkx` version (>="3.4rc0").

## [0.10.0] - 2024-10-04

### Added

- New optional field `requirements` in the `graph` field of the graph schema. This field contain a
  list of projects that should be present in the Python environment for the graph to be executed.

## [0.9.0] - 2024-09-16

### Added

- Script tasks: support positional arguments.

### Changed

- Script tasks: use "-" for single-character and "--" for multi-character script parameter names.
- The EWOKS events are send to EWOKS event handlers and to a normal application logger.

## [0.8.1] - 2024-09-14

### Added

- `load_graph` is now able to load non-JSON files from a path without extension.
- `load_graph` and `convert_graph` accept now `Path` type args for the workflow path and the root directory.
- New method `cancel` in `Task` to be called when the task must be cancelled. It is up to each `Task` to implement this method.
- New field `force_start_node` for graph nodes. Setting this field to `True` forcefully marks
  the node as a start node (i.e. a node that must be executed before others).

### Deprecated

- `ewokscore.graph.serialize`: `ewoks_jsonload_hook` is deprecated. Use `json_load` instead.

## [0.8.0] - 2024-09-10 [YANKED]

## [0.7.4] - 2024-06-12

### Fixed

- The pyyaml 6.0.2rc1 package is broken for python 3.7 or lower.

## [0.7.3] - 2024-03-13

### Changed

- Numpy 2.0 is not supported.

## [0.7.2] - 2024-03-13

### Changed

- Replace deprecated pkg_resources.

## [0.7.1] - 2023-07-04

### Changed

- Make notebook test flaky for python 3.7.

## [0.7.0] - 2023-07-03

### Added

- Add support for jupyter notebooks as workflow tasks.

## [0.6.1] - 2023-06-20

### Changed

- Executable scripts absolute path before execution.

## [0.6.0] - 2023-06-20

### Changed

- Support executable scripts on linux (scripts that have a shebang).

## [0.5.3] - 2023-06-19

### Changed

- Modify task doc strings.

## [0.5.2] - 2023-06-12

### Changed

- Remove print statement from the task_discovery module.

## [0.5.1] - 2023-06-09

### Changed

- By default, task discovery raises import errors when modules are specified and
  logs import errors when importing all tasks.

## [0.5.0] - 2023-06-09

### Added

- Task discovery without the need to specify modules (using package entry points).

## [0.4.3] - 2023-06-01

### Added

- Module can optionally be reloaded when discovering tasks.

## [0.4.2] - 2023-06-01

### Added

- Module can optionally be reloaded when discovering tasks.

## [0.4.1] - 2023-05-15

### Deprecated

- Task properties that instantiate objects whenever used are replaced by functions.

## [0.4.0] - 2023-03-27

### Added

- CLI support inputs by label or task identifier.

### Changed

- CLI option "--output" renamed to "--outputs".

## [0.3.3] - 2023-03-24

### Changed

- Tasks discovery includes the current working directory.

## [0.3.2] - 2023-03-23

### Changed

- Make discover_tasks_from_modules pickelable.

## [0.3.1] - 2023-03-08

### Deprecated

- Ewoks event field "binding" is deprecated in favor of "engine".

## [0.3.0] - 2022-11-04

### Changed

- `Variable` methods `variable_values`, `named_variable_values`, `positional_variable_values`
  no longer values of type `MissingData`.

## [0.2.1] - 2022-10-28

### Fixed

- Store only "name" and "value" of dynamic inputs in node default inputs.

## [0.2.0] - 2022-10-26

### Added

- Workflow inputs and outputs: use `task_identifier` to select nodes.

## [0.1.1] - 2022-09-02

### Fixed

- Add missing `packaging` dependency.

## [0.1.0] - 2022-08-31

### Added

- `Graph` class as an API for all task graphs.
- `Task` class as an API for all tasks.
- `Variable` class for task parameters, hashing and persistence (JSON, HDF5-Nexus).
- `load_graph` for loading graph from JSON or YAML.
- `execute_graph` for naive task scheduling in a single thread.
- Execution events based on python's logging facility.

[unreleased]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v2.0.0...HEAD
[2.0.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v1.6.0...v2.0.0
[1.6.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v1.5.0...v1.6.0
[1.5.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v1.4.0...v1.5.0
[1.4.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v1.3.0...v1.4.0
[1.3.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v1.2.0...v1.3.0
[1.2.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v1.1.0...v1.2.0
[1.1.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v1.0.0...v1.1.0
[1.0.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.15.0...v1.0.0
[0.15.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.14.0...v0.15.0
[0.14.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.13.1...v0.14.0
[0.13.1]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.13.0...v0.13.1
[0.13.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.12.0...v0.13.0
[0.12.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.11.0...v0.12.0
[0.11.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.10.0...v0.11.0
[0.10.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.9.0...v0.10.0
[0.9.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.8.1...v0.9.0
[0.8.1]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.8.0...v0.8.1
[0.8.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.7.4...v0.8.0
[0.7.4]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.7.3...v0.7.4
[0.7.3]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.7.2...v0.7.3
[0.7.2]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.7.1...v0.7.2
[0.7.1]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.7.0...v0.7.1
[0.7.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.6.1...v0.7.0
[0.6.1]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.6.0...v0.6.1
[0.6.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.5.3...v0.6.0
[0.5.3]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.5.2...v0.5.3
[0.5.2]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.5.1...v0.5.2
[0.5.1]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.5.0...v0.5.1
[0.5.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.4.3...v0.5.0
[0.4.3]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.4.2...v0.4.3
[0.4.2]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.4.1...v0.4.2
[0.4.1]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.4.0...v0.4.1
[0.4.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.3.3...v0.4.0
[0.3.3]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.3.2...v0.3.3
[0.3.2]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.3.1...v0.3.2
[0.3.1]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.3.0...v0.3.1
[0.3.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.2.1...v0.3.0
[0.2.1]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.2.0...v0.2.1
[0.2.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.1.1...v0.2.0
[0.1.1]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/compare/v0.1.0...v0.1.1
[0.1.0]: https://gitlab.esrf.fr/workflow/ewoks/ewokscore/-/tags/v0.1.0
