ewokscore |version|
===================

*ewokscore* provides an API to define workflows and implement tasks in `ewoks <https://ewoks.readthedocs.io/>`_.

*ewokscore* has been developed by the `Software group <http://www.esrf.eu/Instrumentation/software>`_ of the `European Synchrotron <https://www.esrf.eu/>`_.

Getting started
---------------

Install requirements

.. code:: bash

    pip install ewokscore

Execute a workflow

.. code:: python

    from ewokscore import execute_graph

    result = execute_graph("/path/to/graph.json")

Run the tests

.. code:: bash

    pip install ewokscore[test]
    pytest --pyargs ewokscore.tests

Documentation
-------------

.. toctree::
    :maxdepth: 2

    hello_world
    definitions
    execute_io
    implementation
    events
    api
