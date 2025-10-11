Workflow implementation
=======================

Workflows in `ewoks` are based on *networkx* graphs, both in terms of runtime representation and
persistent representation. At runtime, links between nodes are hash links which provide a unique
identifier for each task output. This identifier is used to save and load task outputs from external
storage (e.g. HDF5).

Hash links
----------

Hash links between tasks have these requirements:

* changing task input values or links will change all output hashes of the downstream tasks and hence
  also their URI's to external storage
* pass the actual data from one task to another or the associated URI's should result in the
  same outcome
* task results should never be hashed because they can be large

Hash implementation
-------------------

The *universal hashing* in *ewoks* is currently based on SHA-256. The `UniversalHash` class
representation a *universal hash* at runtime. Several builtin python types are *universally hasheable*:
strings, numbers, mappings, sets and iterables. Custom types that are *universally hasheable* should
derive from `UniversalHashable`.

Tasks and task inputs and outputs are *universally hasheable* and are implementation as described
in this class diagram:

.. mermaid::

   classDiagram
      UniversalHashable <|-- Variable
      Variable <|-- VariableContainer
      Variable --o VariableContainer
      UniversalHashable <|-- Task
      Task o-- VariableContainer
      class UniversalHashable{
          -version
          -class_nonce
          #pre_uhash
          #class_uhash
          #instance_nonce
          #data_uhash()
          uhash() UniversalHash
      }
      class Variable{
          value
          data_proxy: DataProxy
      }
      class VariableContainer{
          value: Dictionary<string|int, Variable>
      }
      class Task{
          input_variables: VariableContainer
          output_variables: VariableContainer
      }

UniversalHashable
+++++++++++++++++

The return value of `UniversalHashable.uhash()` can be either

* the *universal hash* of `pre_uhash` and `instance_nonce` when `instance_nonce`
  is provided on instantiation
* equal to `pre_uhash` when `instance_nonce` is NOT provided on instantiation

The value of `UniversalHashable.pre_uhash` can be either

* provided on instantiation
* the *universal hash* of `UniversalHashable.class_nonce` and the return value of `UniversalHashable.data_uhash()`

The value of `UniversalHashable.class_nonce` is the *universal hash* of

* the class full qualifier name
* `UniversalHashable.version`
* `UniversalHashable.class_nonce` of the base class

Variable
++++++++

The return value of  `Variable.data_uhash()` is `Variable.value` or `None` when hashing is disabled.

The `Variable.data_proxy` provides read-write access to the `Variable` data in external storage.

A `DataProxy` generates a `DataUri` for a root URI and a `UniversalHashable` (in this case a `Variable`).

For example when the root URI is `"/tmp/dataset_name.nx?path=scan_name/task_results/var1"` then the
`DataUri` will look like this

* `.json:///tmp/dataset_name/scan_name/task_results/var1/6872c154c80bfcda0a9a769e3c1b4c85b8a56ad8d022d5c5da3ef9c036bc1e01.json`
* `.nexus:///tmp/dataset_name.nx?path=scan_name/task_results/var1/6872c154c80bfcda0a9a769e3c1b4c85b8a56ad8d022d5c5da3ef9c036bc1e01`

Example:
++++++++

A task which takes a single integer as input and an array as output

.. code-block:: python

  class MyTask(Task, input_names=["N"], output_names=["array"]):

    def run(self):
      self.outputs.array = random(self.inputs.N)

When instantiating `MyTask`, the following happens

.. code-block:: python

   self.input_variables = VariableContainer(value={"N": N})
   self.output_variables = VariableContainer(value={"array": self.MISSING_DATA},
                                             pre_uhash=input_variables,
                                             instance_nonce=self.class_nonce())
   self.pre_uhash = self.output_variables

The *universal hash* of the task is equal to the *universal hash* of the output container.

The input variable container instantiates this variable

.. code-block:: python

  input_variables["N"] = Variable(value=100000)
  # N is a `Variable` (task input in this case)
  # It’s value is 100000
  # It’s uhash is calculated from the value

The output variable container instantiates this variable

.. code-block:: python

  output_variables["array"] = Variable(value=output_variables.MISSING_DATA,
                                       pre_uhash=output_variables.pre_uhash,
                                       instance_nonce=(output_variables.instance_nonce, "array"))
  # array is a `Variable` (task output in this case)
  # It’s value is not yet defined (set in the `run` method)
  # It’s uhash is not calculated from the value but from the uhash of the task input container

This scheme ensures that the hash of a single output variable depends on all upstream inputs
and does not depend on its value . The output variables take the `MyTask.class_nonce()` as an
instance nonce to ensure that different tasks with identical upstream inputs produce.
