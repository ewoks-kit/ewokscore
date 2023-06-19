# CHANGELOG.md

## 0.6.0 (unreleased)

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
