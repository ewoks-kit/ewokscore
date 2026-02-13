Workflow definition
===================

A **workflow** is a directed graph of tasks. A directed graph consists of nodes and links.

A **node** describes an opaque unit of execution with a signature. It can have positional and named
arguments which can be required or optional. It can have zero, one or more named outputs.

A **task** is an opaque unit of execution with input arguments defined by links and default values
in the graph representation. (OOP analogy: a task is a node instance).

A **link** connects a source node to a target node. A link can have the following properties:
  * **conditional**: has a set of statements that combined are either True or False
  * **required**: either "marked as required” in the graph representation" or “unconditional
    and all ancestors of the source node are required”
  * **data_mapping**: describes data transfer from source to target.

Task scheduling
---------------

A task can only be executed when all required predecessors have been executed successfully.

Task scheduling starts by executing all **start tasks**. When a graph has nodes without predecessors,
those are the start tasks. Otherwise all nodes without required predecessors and with all required
arguments statically defined are start nodes.

The input arguments of a task are defined in the following order of priority:
 * Input from non-required predecessors (we allow maximum one of those)
 * Input from all unconditional links (argument collisions raise an exception)
 * Input from the graph representation (default input)

*ewokscore* has a native, sequential task scheduler which can be used like this

.. code-block:: python

  from ewokscore import execute_graph

  result = execute_graph("/path/to/graph.json")


The `execute_graph` method can be imported from the *ewoks* binding projects for more complex task scheduling.

Graph definition
----------------

*Ewoks* describes workflows as a list of nodes and a list of links with specific attributes
(we show the JSON representation)

.. code-block:: json

    {
        "graph": {"id": "mygraph"}
        "nodes": [{"id": "name1",
                   "task_type": "class",
                   "task_identifier": "package.module.task.SumTask",
                   "default_inputs": [{"name":"a", "value":1}]},
                  {"id": "name2",
                   "task_type": "class",
                   "task_identifier": "package.module.task.SumTask"}]
        "links": [{"source": "name1",
                   "target": "name2",
                   "data_mapping":[{"source_output":"result",
                                    "target_input":"a"}]}],
    }

Graph attributes
^^^^^^^^^^^^^^^^
* *id* (optional): graph identifier unique to a database of graphs (Default: "notspecified")
* *label* (optional): non-unique label to be used when identifying a graph for human consumption
* *schema_version* (optional): the schema version of this graph representation (Default: "1.0")
* *requirements* (optional): a list of projects that should be present in the Python environment for the 
  graph to be executed.
* *input_nodes* (optional): nodes that are expected to be used as link targets when the graph
  is used as a subgraph.
* *output_nodes* (optional): nodes that are expected to be used as link sources when the graph
  is used as a subgraph.

The *input_nodes* and *output_nodes* have these attributes

* *id*: non-unique node identifier which will be used in links with a super graph. When there are
  multiple nodes with the same *id*, a single link will be expanded to multiple links at runtime.
* *node*: node identifier which should be in the node attributes of this graphs
* *sub_node* (optional): in case *node* is a graph we need to specify the node *id* inside
  that graph. The *sub_node* can be an *id* from the node attributes of the sub-graph or
  from sub-graph attributes *input_nodes* or *output_nodes*.
* *link_attributes* (optional): default link attributes used in links with a super graph. The
  link attributes specified in the super graph have priority over these defaults.

For example for a graph with normal nodes `"id1"` and `"id3"` and a sub-graph node `"id2"`
which in turn has an input node `"start"` and output node `"end"`:

.. code-block:: json

    {
        "graph": {
            "label": "subgraph",
            "input_nodes": [
                {"id": "in1", "node": "id1"},
                {"id": "in2", "node": "id2", "sub_node": "start"}
            ],
            "output_nodes": [
                {"id": "out1", "node": "id3"},
                {"id": "out2", "node": "id2", "sub_node": "end"}
            ]
        }
        "nodes": [
            {"id": "id1", "task_type": "class", "task_identifier": "..."},
            {"id": "id2", "task_type": "graph", "task_identifier": "..."},
            {"id": "id3", "task_type": "class", "task_identifier": "..."},
        ]
    }

The `"in*"` and `"out*"` id's can be used by a super-graph when making connections. For example

.. code-block:: json

    {
        "graph": {
            "label": "supergraph"
        }
        "nodes": [
            {"id": "id1", "task_type": "class", "task_identifier": "..."},
            {"id": "id2", "task_type": "graph", "task_identifier": "subgraph.json"},
            {"id": "id3", "task_type": "class", "task_identifier": "..."}
        ]
        "links": [
            {"source": "id1", "target": "id2", "sub_target":"in1"},
            {"source": "id2", "sub_source":"out2", "target": "id3"},
        ]
    }

Node attributes
^^^^^^^^^^^^^^^
* *id*: node identifier unique to the graph
* *label* (optional): non-unique label to be used when identifying a node for human consumption
* *task_identifier*: specifies the unit of execution
* *task_type*: defines the meaning of *task_identifier* and can have of these values:

  * *class*: *task_identifier* is the full qualifier name of a task class (statically defined)
  * *generated*: *task_identifier* is an argument that is used by *task_generator* to generate
    a task at runtime
  * *method*: *task_identifier* is the full qualifier name of a function
  * *graph*: *task_identifier* is the representation of another graph (e.g. json file name)
  * *ppfmethod*: *task_identifier* is the full qualifier name of a *pypushflow* function (special input/output convention)
  * *ppfport*: special *ppfmethod* which is the *identify mapping*. *task_identifier* should not be specified.
  * *script*: *task_identifier* is the absolute path of a python or shell script
  * *notebook*: *task_identifier* is the absolute path of a jupyter notebook
* *task_generator* (optional): the full qualifier name of a method that generates a task at runtime
  based on *task_identifier*. Only used when *task_type* is *generated*.
* *default_inputs* (optional): default input arguments (used when not provided by the output of other tasks). For example:
    .. code-block:: json

        {
            "default_inputs": [{"name":"a", "value":1}]
        }
* *force_start_node* (optional): when set to `True`, the node will be forcefully defined as a start node i.e. a node that should be executed before all others 
(to be used as an escape hatch when the graph analysis fails to correctly assert the start nodes).
* *conditions_else_value* (optional): value used in conditional links to indicate the *else* value (Default: `None`)
* *default_error_node* (optional): when set to `True` all nodes without error handler will be linked to this node.
* *default_error_attributes* (optional): when `default_error_node=True` this dictionary is used as attributes for the
  error handler links. The default is `{"map_all_data": True}`. The link attribute `"on_error"` is forced to be `True`.

Link attributes
^^^^^^^^^^^^^^^
* *source*: the *id* of the source node
* *sub_source*: when *source* is a *graph*, specify the *id* or `output_nodes` alias of the node in *source*
* *target*: the *id* of the target node
* *sub_target*: when *target* is a *graph*, specify the *id* of `input_nodes` alias of the node in *target*
* *sub_target_attributes* (optional): can be used when *target* is a *graph*. It allows changing the node
  attributes of *sub_target* in the sub-graph.
* *data_mapping* (optional): describe data transfer from source outputs to target input arguments. For example
    .. code-block:: json

        {
            "data_mapping": [{"source_output": "result",
                              "target_input": "a"}]
        }

    If `"source_output"` is `None` or missing, the complete output of the source will be passed to the corresponding
    `"target_input"` or the target.
* *map_all_data* (optional): setting this to `True` is equivalent to *data_mapping* being the identity mapping for
  all input names. Cannot be used in combination with *data_mapping*.
* *conditions* (optional): provides a list of expected values for source outputs
    .. code-block:: json

        {
            "conditions": [{"source_output": "result", "value": 10}]
        }
* *on_error* (optional): a special condition "the source task raises an exception". Cannot be used in combination with *conditions*.
* *required* (optional): setting this to `True` marks the link as *required*. When a target receives multiple links, it will be executed
  (perhaps multiple times) when all the sources connected to the target with *required* links have been executed. A link is required when
  it is either "marked as required" (link attribute `required=True`) or “unconditional and all ancestors of the source node are required”.

Task implementation
-------------------
All tasks can be described by deriving a class from the `Task` class.

* required input names: an exception is raised when these inputs are not provided in the graph definition
  (output from previous tasks or default input values)
* optional input names: no default values provided (need to be done in the `process` method)
* output names: can be connected to downstream input names
* required positional inputs: a positive number

For example

.. code-block:: python

    from ewokscore import Task

    class SumTask(
        Task,
        input_names=["a"],
        optional_input_names=["b"],
        output_names=["result"]
    ):
        def run(self):
            result = self.inputs.a
            if self.inputs.b:
                result += self.inputs.b
            self.outputs.result = result

When a task is defined as a method, script or notebook, a class wrapper will be generated automatically:

* *method*: defined by a `Task` class with one required input argument ("_method": full qualifier name of the method)
  and one output argument ("return_value")
* *ppfmethod*: same as *method* but it has one optional input "_ppfdict" and one output "_ppfdict". The output
  dictonary is the input dictionary updated by the method. The input dictionary is unpacked before passing to the method.
  The output dictionary is unpacked when checking conditions in links.
* *ppfport*: *ppfmethod* which is the identity mapping
* *script*: defined by a `Task` class with one required input argument ("_script": path to the script)
  and one output argument ("return_code")
* *notebook*: defined by a `Task` class with one required input argument ("_notebook": path to the notebook)
  and two output arguments ("results" and "output_notebook")
