import logging
from ewoksutils.event_utils import FIELD_TYPES

__all__ = ["is_ewoks_event_handler", "EwoksEventHandlerMixIn", "EwoksEventHandler"]


def is_ewoks_event_handler(handler):
    return isinstance(handler, EwoksEventHandlerMixIn)


class EwoksEventHandlerMixIn:
    BLOCKING = False
    FIELD_TYPES = FIELD_TYPES


class EwoksEventHandler(EwoksEventHandlerMixIn, logging.Handler):
    """Base class for handling ewoks events on the publishing side (implement the `emit` method)."""

    pass
