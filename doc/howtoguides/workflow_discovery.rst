Workflow discovery
==================

All ewoks workflows provided by one or more python modules can be discovered as follows

.. code-block:: python

    from ewokscore.workflow_discovery import discover_workflows_from_modules

    workflows = discover_workflows_from_modules(
        "myproject.workflows.*",
        "myproject.subpackage.demo.*",
        workflow_extension="json",
    )

The `workflow_extension` can have one of these values

* `"json"`: discover JSON workflow resources
* `"yaml"`: discover YAML workflow resources
* `None` (default): discover both JSON and YAML workflow resources

Module names can contain wildcards `"*"`.

For example

.. code-block:: python

    workflows = discover_workflows_from_modules(
        "myproject.*.workflows.*"
    )

could discover workflows such as

.. code-block:: text

    myproject.module1.workflows.graph1
    myproject.module2.workflows.graph2

corresponding to resource files like

.. code-block:: text

    myproject/module1/workflows/graph1.json
    myproject/module2/workflows/graph2.yaml

The wildcard `"*"` matches exactly one package or workflow name component.

To discover all workflows provided by all installed python packages

.. code-block:: python

    from ewokscore.workflow_discovery import discover_all_workflows

    workflows = discover_all_workflows(workflow_extension="yaml")

For this to work the package that provides ewoks workflows should declare its workflow modules
via the entry point mechanism.

.. code-block:: toml

    # pyproject.toml

    [project.entry-points."ewoks.workflows"]
    "myproject.workflows.*" = "myproject1"
    "myproject.*.demo.*" = "myproject2"

The group name must be `"ewoks.workflows"`.

The keys are the module patterns in which to discover workflows. The values are ignored but need
to be globally unique because of the way entry points work.

The workflow discovery mechanism searches for workflow resource files inside python packages.
For example, the entry point

.. code-block:: toml

    [project.entry-points."ewoks.workflows"]
    "myproject.workflows.*" = "myproject1"

can discover workflow resources such as

.. code-block:: text

    myproject/workflows/example.json
    myproject/workflows/demo.yaml

A project that provides ewoks workflows can also add the `"ewoks"` keyword to be discoverable in
a package repository like PyPI:

.. code-block:: toml

    # pyproject.toml

    [project]
    name = "myproject"
    keywords = ["ewoks"]
