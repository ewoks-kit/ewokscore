Workflow inputs and outputs
===========================

Workflow inputs and outputs can be provided when executing a workflow

.. code:: python

    from ewokscore import execute_graph

    results = execute_graph(
        "/path/to/file.json",
        inputs=[{...}, {...}, ...],   # list of dictionaries
        outputs=[{...}, {...}, ...]   # list of dictionaries
    )

The dictionary keys for inputs are

* name: input variable name
* value: input variable value
* id (optional): node id
* label (optional): used when `id` is missing
* task_identifier (optional): used when `id` is missing (the node's task identifier must end with this string)
* all (optional): used when `id`, `label` and `task_identifier` are missing (`True`: all nodes, `False`: start nodes)

An example to provide the following input arguments to the workflow nodes

* node with id `task1` receive `a=10`
* node with label `My Node` receive `b=20`
* all start nodes receive `collectionId=1234`
* all `mypackage.mymodule.IntegrationTask` tasks receive `nbpts_azi=1024`

.. code:: python

    from ewokscore import execute_graph

    results = execute_graph(
        "/path/to/file.json",
        inputs=[{"id": "task1", "name":"a", "value": 10},
                {"label": "My Node", "name":"b", "value": 20},
                {"name":"collectionId", "value": 1234},
                {"task_identifier": "IntegrationTask", "name":"nbpts_azi", "value": 1024}]
    )

The dictionary keys for outputs are

* name (optional): output variable name (all outputs when missing)
* new_name (optional): optional renaming when `name` is defined (can be used avoid naming collisions)
* id (optional): node id
* label (optional): used when `id` is missing
* task_identifier (optional): used when `id` is missing (the node's task identifier must end with this string)
* all (optional): used when `id`, `label` and `task_identifier` are missing (`True`: all nodes, `False`: end nodes)

When no outputs are provided, the output variables of all *end nodes* are returned

.. code:: python

    from ewokscore import execute_graph

    results = execute_graph(
        "/path/to/file.json",
        outputs=[{"all": False}]
    )

An example where we use the return value of two tasks as the workflow output

.. code:: python

    from ewokscore import execute_graph

    results = execute_graph(
        "/path/to/file.json",
        inputs=[{"id": "task1", "name": "return_value", "new_name": "return_value1"},
                {"id": "task2", "name": "return_value", "new_name": "return_value2"}]
    )

    assert set(results) == {"return_value1", "return_value2"}
