Python function as workflow task
================================

A Python function can be used as a task node in a workflow by using ``"method"`` as its ``task_type``.
By default, such task has a single output named ``return_value``.
It is possible to `Define multiple outputs`_.

Use a function as a task
------------------------

Example with a ``range_info`` function returning 3 values in a dictionary:

.. code:: python

    def range_info(a: float, b: float):
        return {
            "extent": abs(b - a),
            "minimum": min(a, b),
            "maximum": max(a, b),
        }

The corresponding workflow node must be declared with ``"method"`` as ``task_type``:

.. code:: python

    range_info_node = {
        "id": "task_range_info",
        "task_type": "method",
        "task_identifier": "__main__.range_info",
    }

Code to execute the ``range_info`` function as a task in a workflow with ``a=15`` and ``b=10`` as inputs:

.. code:: python

    from ewokscore import execute_graph

    # Define a workflow which calls the range_info function as a task
    workflow = {
        "graph": {"id": "range_info_workflow"},
        "nodes": [
            {
                "id": "task_range_info",
                "task_type": "method",
                "task_identifier": "__main__.range_info",
            },
        ],
        "links": [],
    }

    # Define task inputs
    inputs = [
        {"id": "task_range_info", "name": "a", "value": 15},
        {"id": "task_range_info", "name": "b", "value": 10},
    ]

    # Execute the workflow
    result = execute_graph(workflow, inputs=inputs)
    print(result)

The task output contains a single ``return_value`` field which is set to the function return value.

In the ``range_info`` example, the result contains a single output field ``return_value``:

.. code:: python

    {'return_value': {'extent': 5, 'minimum': 10, 'maximum': 15}}


Define multiple outputs
-----------------------

To declare a function that can be used as a :class:`Task` with multiple output fields:

* Declare the function with one of the following kind of return type:

  .. tab-set::

      .. tab-item:: namedtuple

          .. code:: python

              from collections import namedtuple

              Result = namedtuple("Result", ["extent", "minimum", "maximum"])

      .. tab-item:: dataclass

          .. code:: python

              from dataclasses import dataclass

              @dataclass
              class Result:
                  extent: float
                  minimum: float
                  maximum: float

      .. tab-item:: typing.NamedTuple

          .. code:: python

              from typing import NamedTuple

              class Result(NamedTuple):
                  extent: float
                  minimum: float
                  maximum: float

      .. tab-item:: typing.TypedDict

          .. code:: python

              from typing import TypedDict

              class Result(TypedDict):
                  extent: float
                  minimum: float
                  maximum: float

  .. code:: python

      def range_info(a: float, b: float) -> Result:

* Add the :func:`task_outputs` decorator to the function declaration:

  .. code:: python

      from ewokscore.methodtask import task_outputs

      @task_outputs
      def range_info(a: float, b: float) -> Result:
          return Result(
              extent=abs(b - a),
              minimum=min(a, b),
              maximum=max(a, b),
          )


When a ``@task_outputs`` decorated function is used as a :class:`Task`, the task output names are defined by the function return type.

In the example, the return value of ``range_info`` function is available through 3 task outputs:

.. code:: python

    {'maximum': 15, 'extent': 5, 'minimum': 10}
