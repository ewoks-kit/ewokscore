import logging
from . import send_events
from ..logging_utils import handlers


def is_ewoks_event_handler(handler):
    return isinstance(handler, EwoksEventHandlerMixIn)


class EwoksEventHandlerMixIn:
    BLOCKING = False


class EwoksEventHandler(EwoksEventHandlerMixIn, logging.Handler):
    pass


class EwoksSqlite3EventHandler(EwoksEventHandlerMixIn, handlers.Sqlite3Handler):
    def __init__(self, uri: str):
        super().__init__(uri=uri, table="ewoks_events", fields=send_events.FIELDS)
