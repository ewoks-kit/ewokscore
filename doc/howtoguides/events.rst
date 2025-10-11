Workflow events
===============

Events are emitted when executing a workflow. The event fields are described in
the `ewoksutils <https://ewoksutils.readthedocs.io/>`_ documentation.

Use an Ewoks event handler
--------------------------

If you want to record workflow events you have to specify one or more event handlers when executing a workflow:

.. code-block:: python

    from ewokscore import execute_graph

    execinfo = {
        "job_id": "1234",
        "handlers": [
            {
                "class": "ewokscore.events.handlers.Sqlite3EwoksEventHandler",
                "asynchronous": True,
                "arguments": [{"name": "uri",
                               "value": "file:/tmp/ewoks_event.db"}],
            }
        ],
    }
    results = execute_graph("/path/to/file.json", execinfo=execinfo)

The optional `asynchronous` argument should be used for handlers with slow connections. Setting this
argument to `True` will send events to the handlers in a separate thread.

Define an Ewoks event handler
-----------------------------

You can use any handler derived from `logging.Handler` as an Ewoks event handler. For example if you
have a `Connection` class with a constructor that accepts two arguments, you can define an ewoks
event handler as follows:

.. code-block:: python

    # ./myproject/handlers.py

    from ewokscore.logging_utils.handlers import ConnectionHandler
    from ewokscore.handlers import send_events
    from ewokscore.events import EwoksEventHandlerMixIn

    class MyHandler(EwoksEventHandlerMixIn, ConnectionHandler):

        def _connect(self, uri:str, param1:int, timeout=1) -> None:
            self._connection = Connection(uri, param1)
            self._fields = send_events.FIELDS

        def _disconnect(self) -> None:
            del self._connection
            self._connection = None

        def _send_serialized_record(self, srecord):
            self._connection.send(srecord)

        def _serialize_record(self, record):
            return {
                field: self.get_value(record, field, None) for field in self._fields
            }

`ConnectionHandler` is an abstract python logging handler which can be used for convenience.

To use this example handler

.. code-block:: python

    from ewokscore import execute_graph

    execinfo = {
        "job_id": "1234",
        "handlers": [
            {
                "class": "myproject.handlers.MyHandler",
                "arguments": [{"name": "uri",
                               "value": "file:/tmp/ewoks_event.db"},
                              {"name": "param1", "value": 10}],
            }
        ],
    }
    results = execute_graph("/path/to/file.json", execinfo=execinfo)
