Workflow events
===============

Events are emitted when executing a workflow. The event fields are

+------------------+-------------------+------------------------+-------------------------------------+
| Field            | Type              | Not None when          | Value                               |
+==================+===================+========================+=====================================+
| host_name        | str               |                        |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| process_id       | int               |                        |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| user_name        | str               |                        |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| job_id           | str               |                        | random uuid by default              |
+------------------+-------------------+------------------------+-------------------------------------+
| binding          | str\|None         | using a scheduler      |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| context          | str               |                        | `"workflow"` or `"node"`            |
+------------------+-------------------+------------------------+-------------------------------------+
| workflow_id      | str               |                        |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| node_id          | str\|None         | `context == "node"`    |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| task_id          | str\|None         | `context == "node"`    |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| type             | str               |                        | `"start"`, `"end"` or `"progress"`  |
+------------------+-------------------+------------------------+-------------------------------------+
| time             | str               |                        | ISO 8601 format in local timezone   |
+------------------+-------------------+------------------------+-------------------------------------+
| error            | bool\|None        | `event == "end"`       |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| error_message    | str\|None         | `event == "end"`       |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| error_traceback  | str\|None         | `event == "end"`       |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| progress         | int\|None         | `event == "progress"`  | number between 0 and 100            |
+------------------+-------------------+------------------------+-------------------------------------+
| task_uri         | str\|None         |                        |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| input_uris       | List[Dict]\|None  | `event == "start"`     |                                     |
+------------------+-------------------+------------------------+-------------------------------------+
| output_uris      | List[Dict]\|None  | `event == "start"`     |                                     |
+------------------+-------------------+------------------------+-------------------------------------+

Use an Ewoks event handler
--------------------------

If you want to record workflow events you have to specify one or more event handlers when executing a workflow:

.. code:: python

    from ewokscore import execute_graph

    execinfo = {
        "job_id": "1234",
        "handlers": [
            {
                "class": "ewokscore.events.handlers.EwoksSqlite3EventHandler",
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

.. code:: python

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

.. code:: python

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
