# CHANGELOG.md

## 0.2.0 (unreleased)

## 0.1.0

Added:
  - `Graph` class as an API for all task graphs
  - `Task` class as an API for all tasks
  - `Variable` class for task parameters, hashing and
     persistence (JSON, HDF5-Nexus)
  - `load_graph` for loading graph from JSON or YAML
  - `execute_graph` for naive task scheduling in a single thread
  - Execution events based on python's logging facility
