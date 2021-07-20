# EwoksCore: API for graphs and tasks in Ewoks

## Workflow definition

A **workflow** is a directed graph of tasks. A directed graph consists of nodes and links.

A **node** describes an opaque unit of execution with a signature. It can have positional and named arguments which can be required or optional. It can have zero, one or more named outputs.

A **task** is an opaque unit of execution with input arguments defined by links and static values in the graph representation. (OOP analogy: a task is a node instance).

A **link** connects a source node to a target node. A link can have the following properties:
 * **conditional**: has a set of statements that combined are either True or False
 * **required**: either marked as “required” in the graph representation or “unconditional and all ancestors of the source node are required”
  * **arguments**: a mapping from input arguments of the target to output arguments of the source.

### Task scheduling

A task can only be executed when all required predecessors have been executed successfully.

Task scheduling starts by executing all **start tasks**. When a graph has nodes without predecessors, those are the start tasks. Otherwise all nodes without required predecessors and with all required arguments statically defined are start nodes.

The input arguments of a task are defined in the following order of priority:
 * Input from non-required predecessors (we allow maximum one of those)
 * Input from all unconditional links (argument collisions raise an exception)
 * Input from the graph representation (static input)

## Workflow description

Ewoks describes workflows as a list of nodes and a list of links

```json
{
    "nodes": [{"id": "nodeid1", ...},
              {"id": "nodeid2", ...},
              ...],
    "links": [{"source": "nodeid1", "target": "nodeid2", ...},
              ...],
}
```

Each node and link can have the following attributes.

### Graph attributes
* *nodes*: a list of nodes
* *links*: a list of links
* *name* (optional): the name of the task graph

### Node attributes
 * *id*: node identifier unique to the graph
 * Only **one** of these attributes to specify the unit of execution:
    * *class*: the full qualifier name of a task class
    * *method*: the full qualifier name of a function
    * *ppfmethod*: the full qualifier name of a pypushflow function (special input/output convention)
    * *script*: the full qualifier name of a python or shell script
    * *graph*: the representation of another graph (e.g. json file name)
 * *inputs* (optional): static input arguments (for example `{"a": 1}`)
 * *inputs_complete* (optional): set to `True` when the static input covers all required input (used for method and script as the required inputs are unknown)

### Link attributes
* *source*: the id of the source node 
* *target*: the id of the target node
* *arguments* (optional): a dictionary that maps output names to input names. If the input name is `None` the output name receives the complete output of the source.
* *all_arguments* (optional): setting this to `True` is equivalent to *arguments* being the identity mapping for all input names. Cannot be used in combination with *arguments*.
* *conditions* (optional): a dictionary that maps output names to expected values
* *on_error* (optional): a special condition: task raises an exception. Cannot be used in combination with *conditions*.
* *links*: when source and/or target is a graph, this list of dictionaries specifies the links between the super-graph and the sub-graph. The dictionary keys are
  * *source*: the id of the source node in the sub-graph (ignored when the source is not a graph)
  * *target*: the id of the target node in the sub-graph (ignored when the source is not a graph)
  * *node_attributes* (optional): overwrite the node attributes of the target when the target is a graph

## Task implementation

All tasks can be described by deriving a class from the `Task` class.
* required input names: an exception is raised when these inputs are not provided in the graph definition (output from previous tasks or static input values)
* optional input names: no default values provided (need to be done in the `process` method)
* output names: can be connected to downstream input names
* required positional inputs: a positive number

For example
```python
from ewokscore import Task

class SumTask(
    Task, input_names=["a"], optional_input_names=["b"], output_names=["result"]
):
    def run(self):
        result = self.inputs.a
        if self.inputs.b:
            result += self.inputs.b
        self.outputs.result = result
```

When a task is defined as a method or a script, a class wrapper will be generated automatically:
* *method*: defined by a `Task` class with one required input argument ("method": full qualifier name of the method) and one output argument ("return_value")
* *ppfmethod*: same as *method* but it has one optional input "ppfdict" and one output "ppfdict". The output dictonary is the input dictionary updated by the method. The input dictionary is unpacked before passing to the method. The output dictionary is unpacked when checking conditions in links.
* *ppfport*: *ppfmethod* which is the identity mapping
* *script*: defined by a `Task` class with one required input argument ("method": full qualifier name of the method) and one output argument ("return_value")

## Hash links
The task graph object in `ewokscore` provides additional functionality in top of what *networkx* provides:
* A *Task* can have several positional and named input variables and named output variables.
* A *Task* has a universal hash which is the hash of the inputs with a *Task* nonce.
* An output *Variable* has a universal hash which is the hash of the *Task* with the variable name as nonce.
* An input *Variable* can be
    * static:
        * provided by the persistent *Graph* representation
        * universal hash of the data
    * dynamic:
        * provided by upstream *Tasks* at runtime
        * output *Variable* of the upstream task so it has a universal hash

The actual output data of a *Task* is never hashed. So we assume that if you provide a task with the same input, you will get the same output. Or at the very least it will not be executed again when succeeded once.

Hash linking of tasks serves the following purpose:
* Changing static input upstream in the graph will effectively create new tasks.
* The hashes provide a unique ID to create a *URI* for persistent storage.
* Variables can be provided with universal hashes to replace the hashing of the actual inputs.
* As data can be passed by passing hashes, serialization for distibuted task scheduling can be done efficiently (not much data to serialize) and no special serializer is required to serialize hashes (as they are just strings).

Data management is currently only a proof-of-concept based on JSON files with the universal hashes as file names.
