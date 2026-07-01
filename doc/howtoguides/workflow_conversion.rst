Loading and saving workflows
============================

This tutorial uses a workflow with a single node passing through an object:

.. code-block:: python

    from ewokscore.task import Task

    class PassThroughTask(Task, input_names=["object"], output_names=["object"]):
        def run(self):
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

Workflows can be saved in JSON or YAML format

.. code-block:: python

    from ewokscore import convert_graph

    convert_graph(
        workflow,
        "myresults/workflows.json",
        inputs=[{"id": "task1", "name": "object", "value": 42}],
    )

Loading workflows from JSON or YAML can be done with the same function

.. code-block:: python

    workflow = convert_graph(
        "myresults/workflows.json",
        None,
    )

Conversion between file formats can be done like this

.. code-block:: python

    workflow = convert_graph(
        "myresults/workflows.json",
        "myresults/workflows.yaml",
    )

Workflow representations
------------------------

In short, `convert_graph` allows converting different workflow representations,
either in file or as a Python object in memory (dictionary, string, `TaskGraph`
from ewokscore, `Graph` from networkx). The representation can be provided
explicitly when automatic inference fails

.. code-block:: python

    workflow = convert_graph(
        "myresults/workflows.json",
        "myresults/workflows.yaml",
        load_options={"representation": "json"},
        save_options={"representation": "yaml"},
    )

`ewokscore` supports the following representations:

==================== ================== ==================================
Representation       Data Types         Notes
==================== ================== ==================================
``"json"``           JSON types only    JSON file
``"json_dict"``      Python types       Python dictionary
``"json_string"``    JSON types only    JSON string
``"json_module"``    JSON types only    JSON file distributed in a Python package
``"yaml"``           YAML types only    YAML file
``"test_core"``      Python types       Demo workflows provided by `ewokscore`
==================== ================== ==================================

Serialization
-------------

In case the representation does not support the data type of the `inputs` values,
a `serializer` can be used which will serialize the data before serializing as JSON or YAML
and deserialize after the data is deserialized from JSON or YAML.

For example `json_pickle` allows storing any object in JSON or YAML, in this case a `numpy` array

.. code-block:: python

    import numpy
    from ewokscore import convert_graph

    convert_graph(
        workflow,
        "myresults/workflows.json",
        save_options={"serializer": "json_pickle"},
        inputs=[{"id": "task1", "name": "object", "value": numpy.arange(5)}],
    )

`ewokscore` supports the following serializers:

================== ====================================================
Serializer         Notes
================== ====================================================
``"json"``         Serialize like python's json module
``"json_pickle"``  Preserve native JSON types and pickle all other types
``"hdf5_pickle"``  Preserve native JSON and `numpy` types and pickle all other types
================== ====================================================
