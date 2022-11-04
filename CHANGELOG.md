# CHANGELOG.md

## 0.4.0 (unreleased)

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
