ewokscore |version|
===================

*ewokscore* provides an API to define workflows and implement tasks in `ewoks <https://ewoks.readthedocs.io/>`_.

*ewokscore* has been developed by the `Software group <https://www.esrf.fr/Instrumentation/software>`_ of the `European Synchrotron <https://www.esrf.fr/>`_.

Getting started
---------------

Install requirements

.. code-block:: bash

    pip install ewokscore

Execute a workflow

.. code-block:: python

    from ewokscore import execute_graph

    result = execute_graph("/path/to/graph.json")

Run the tests

.. code-block:: bash

    pip install ewokscore[test]
    pytest --pyargs ewokscore.tests

.. toctree::
    :hidden:

    tutorials/index
    howtoguides/index
    explanations/index
    reference/index
