import logging
from .connection import ConnectionHandler


def is_ewoks_event_handler(handler):
    return isinstance(handler, EwoksEventHanderMixIn)


class EwoksEventHanderMixIn:
    BLOCKING = False


class EwoksEventHander(EwoksEventHanderMixIn, logging.Handler):
    pass


class EwoksConnectionEventHander(EwoksEventHanderMixIn, ConnectionHandler):
    pass
