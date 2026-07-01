Task output caching
===================

This tutorial uses a workflow with a single node passing through an object:

.. code-block:: python

    from ewokscore.task import Task

    class PassThroughTask(Task, input_names=["object"], output_names=["object"]):
        def run(self):
            print("EXECUTED")
            self.outputs.object = self.inputs.object


    workflow = {
        "graph": {"id": "testworkflow", "schema_version": "1.1"},
        "nodes": [
            {
                "id": "task1",
                "task_type": "class",
                "task_identifier": "__main__.PassThroughTask",
            },
        ],
        "links": [],
    }

Task outputs can be cashed by providing an `root_uri` and `scheme`

.. code-block:: python

    from ewokscore import execute_graph

    result = execute_graph(
        workflow,
        varinfo={"root_uri": "myresults", "scheme": "json"},
        inputs=[{"id": "task1", "name": "object", "value": 42}],
    )
    print(result)

`ewokscore` supports `"json"` and `"nexus"` as scheme and the root URI
is a directory or HDF5 URI repespectively. When executing the workflow
twice with the same `inputs`, `PassThroughTask` is not executed the
second time. The result is loaded from the cache when needed, in this case
to be provided as workflow output (which is the default for end-nodes)

.. code-block:: bash

    $ python test.py 
    EXECUTED
    {'object': 42}

    $ python test.py 
    {'object': 42}

When changing at least one input value or an input value to one or more upstream
nodes in the workflow, the task is executed again. In other words the output cache
of a task is unique for the combination of all workflow parameters that could
influence the output values of that task. See :ref:`hash-tree` for implementation
details on how the runtime workflow representation of Ewoks supports this feature.

Any object type is supported through pickling, even when the underlying storage
format does not support it natively. Here is an example of a `numpy` array cached
in JSON format 

.. code-block:: python

    import numpy
    from ewokscore import execute_graph

    result = execute_graph(
        workflow,
        varinfo={"root_uri": "myresults", "scheme": "json"},
        inputs=[{"id": "task1", "name": "object", "value": numpy.arange(5)}],
    )
    print(result)

The `numpy` array is loaded from the JSON cache and unpickled for the second run

.. code-block:: bash

    python test.py 
    EXECUTED
    {'object': array([0, 1, 2, 3, 4])}

    $ python test.py 
    {'object': array([0, 1, 2, 3, 4])}
