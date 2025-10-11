Task discovery
==============

All ewoks tasks provided by one or more python modules can be discovered as follows

.. code-block:: python

    from ewokscore.task_discovery import discover_tasks_from_modules

    tasks = discover_tasks_from_modules("myproject.module1", "myproject.module2", task_type="class")

The `task_type` can have one of these values

* `"class"` (default): the module defines an ewoks task class or imports other modules that define ewoks task classes
* `"method"`: all public methods in the module are assumed to be ewoks tasks
* `"ppfmethod"`: the `"run"` method in the module is assumed to be an ewoks task

To discover all tasks provided by all installed python packages

.. code-block:: python

    from ewokscore.task_discovery import discover_all_tasks

    tasks = discover_all_tasks(task_type="class")

For this to work the package that provides ewoks tasks should declare its task modules
via the entry point mechanism.

.. code-block:: ini

    # setup.cfg

    [options.entry_points]
    ewoks.tasks.class =
        myproject.module1.submoduleA=myproject1
        myproject.*.tasks=myproject2
    ewoks.tasks.method =
        myproject.module3.submodule=myproject3
    ewoks.tasks.ppfmethod =
        myproject.actors.*=myproject4

The group names can be `"ewoks.tasks.class"`, `"ewoks.tasks.method"` or `"ewoks.tasks.ppfmethod"`.
The key are the modules in which to discover tasks. The values are ignored but need to be globally
unique because of the way entry points work. Module names can contain wildcards `"*"`.

A project that provides ewoks tasks can also add the `"ewoks"` keyword to be discoverable in
a package repository like PyPi:

.. code-block:: ini

    # setup.cfg

    [metadata]
    name = myproject
    ...
    keywords =
        ewoks
