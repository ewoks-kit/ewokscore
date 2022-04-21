import logging
from typing import Tuple
from .. import send_events

__all__ = ["is_ewoks_event_handler", "EwoksEventHandlerMixIn", "EwoksEventHandler"]


def is_ewoks_event_handler(handler):
    return isinstance(handler, EwoksEventHandlerMixIn)


class EwoksEventHandlerMixIn:
    BLOCKING = False

    @staticmethod
    def all_fields() -> Tuple[str]:
        return send_events.FIELDS


class EwoksEventHandler(EwoksEventHandlerMixIn, logging.Handler):
    """Base class for handling ewoks events on the publishing side (implement the `emit` method)."""

    pass
