Python function as workflow task
================================

A Python function can be used as a task node in a workflow by using ``"method"`` as its ``task_type``.
By default, such task has a single output named ``return_value``.
It is possible to `Define multiple outputs`_.

Use a function as a task
------------------------

Example with a ``range_info`` function returning 3 values in a dictionary:

.. code:: python

    def range_info(a, b):
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

The task inputs are the arguments of the function, provided by name. An argument without a
default value is a required task input. For arguments that cannot be passed by name, see
`Provide inputs by position`_.

The task output contains a single ``return_value`` field which is set to the function return value.

In the ``range_info`` example, the result contains a single output field ``return_value``:

.. code:: python

    {'return_value': {'extent': 5, 'minimum': 10, 'maximum': 15}}

The docstring of the function describes the task. See :doc:`task_discovery` to make the functions
of a module discoverable as tasks.


Provide inputs by position
--------------------------

An argument that cannot be passed by name is provided as a positional task input, named by its
position:

.. code:: python

    def range_info(a: float, b: float, /):
        ...

.. code:: python

    inputs = [
        {"id": "task_range_info", "name": 0, "value": 15},
        {"id": "task_range_info", "name": 1, "value": 10},
    ]

Positional task inputs are also how a function receives ``*args``:

.. code:: python

    def total(*args):
        return sum(args)

An argument that can be passed by name has to be provided by name. Providing it by position as
well makes the function receive two values for it, which fails the task.

A function with ``**kwargs`` receives every task input that is not one of its arguments.


Define multiple outputs
-----------------------

To declare a function that can be used as a :class:`~ewokscore.task.Task` with multiple output
fields, declare the function with one of the following kind of return type:

.. tab-set::

    .. tab-item:: pydantic model

        .. code:: python

            from ewokscore.model import BaseOutputModel

            class Result(BaseOutputModel):
                extent: float
                minimum: float
                maximum: float

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

    .. tab-item:: namedtuple

        .. code:: python

            from collections import namedtuple

            Result = namedtuple("Result", ["extent", "minimum", "maximum"])

The task output names are then defined by the fields of the return type:

.. code:: python

    def range_info(a: float, b: float) -> Result:
        return Result(
            extent=abs(b - a),
            minimum=min(a, b),
            maximum=max(a, b),
        )

In the example, the return value of the ``range_info`` function is available through 3 task outputs:

.. code:: python

    {'maximum': 15, 'extent': 5, 'minimum': 10}

The function does not have to construct the return type itself. Returning a mapping with the
field names as keys works as well:

.. code:: python

    def range_info(a: float, b: float) -> Result:
        return {
            "extent": abs(b - a),
            "minimum": min(a, b),
            "maximum": max(a, b),
        }

This is also what a :class:`~typing.TypedDict` return type does, as a typed dict is a mapping.


Describe inputs and outputs
---------------------------

Use :func:`~pydantic.Field` to add a description to a task input or output.

Describe a task input with :func:`~pydantic.Field` in the annotation of the corresponding
argument, and a task output in the return type:

.. code:: python

    from typing import Annotated

    from pydantic import Field
    from ewokscore.model import BaseOutputModel


    class Result(BaseOutputModel):
        extent: float = Field(..., description="Distance between the two numbers")
        minimum: float = Field(..., description="Smallest of the two numbers")
        maximum: float = Field(..., description="Largest of the two numbers")


    def range_info(
        a: Annotated[float, Field(description="First number")],
        b: Annotated[float, Field(description="Second number", ge=0)] = 0,
    ) -> Result:
        return Result(
            extent=abs(b - a),
            minimum=min(a, b),
            maximum=max(a, b),
        )

Anything else :func:`~pydantic.Field` provides applies as well. In the example, ``b`` has a
default value which makes it an optional task input, and ``ge=0`` rejects a negative value for it.

A task input can also be described with :func:`~pydantic.Field` as the default value of the
argument:

.. code:: python

    def range_info(
        a: float = Field(..., description="First number"),
        b: float = Field(0, description="Second number", ge=0),
    ) -> Result:

Validate inputs and outputs
---------------------------

The type annotations of the function validate the task inputs and outputs. A task input that
cannot be coerced to the annotated argument type fails the task before the function is called,
and a return value that does not match the return type fails the task after it is called.

Note that annotations coerce as well as validate: an ``int`` input is passed to an argument
annotated as ``float`` as a ``float``.

The task inputs are only validated when every argument of the function can become a field of a
pydantic model. A positional-only, ``*args`` or ``**kwargs`` argument cannot, in which case the
task inputs are passed to the function unvalidated:

.. code:: python

    def range_info(a: float, b: float, **kw) -> Result:  # inputs are not validated

The task outputs are validated in both cases, as the return type does not depend on the
arguments.

Nothing of this is specific to *ewoks*: the function can still be imported and called directly.
Such a direct call is not validated though, because the validation is done by the task.

Validate direct calls
---------------------

Add :func:`~pydantic.validate_call` to validate the arguments and the return value of a direct call
to the function with the same annotations:

.. code:: python

    from pydantic import validate_call


    @validate_call(validate_return=True)
    def range_info(a: float, b: float) -> Result:
        return Result(
            extent=abs(b - a),
            minimum=min(a, b),
            maximum=max(a, b),
        )

.. code:: python

    range_info("not a number", 10)  # ValidationError

The decorator does not change the task: the task inputs and outputs are derived from the
annotations of the undecorated function.

Use its ``config`` argument when an argument is annotated with a type pydantic does not know:

.. code:: python

    from pydantic import ConfigDict


    @validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
    def spectrum_size(data: numpy.ndarray) -> int:
        return data.size


Use a function as a task outside a workflow
-------------------------------------------

The task class of a function is provided by :func:`~ewokscore.methodtask.get_method_task`:

.. code:: python

    from ewokscore.methodtask import get_method_task

    task = get_method_task("__main__.range_info")(inputs={"a": 15, "b": 10})
    task.execute()
    print(task.get_output_values())

.. code:: python

    {'extent': 5, 'minimum': 10, 'maximum': 15}
