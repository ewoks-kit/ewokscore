"""Manage the ewoks event logger which is a global object
"""

import os
import logging
from contextlib import contextmanager
from typing import Dict, Iterable, List, Optional, Tuple

from ewoksutils.logging_utils.asyncwrapper import AsyncHandlerWrapper
from ewoksutils.logging_utils.cleanup import cleanup_logger

from .handlers import is_ewoks_event_handler, instantiate_handler

EWOKS_EVENT_LOGGER_NAME = __name__
ENABLE_EWOKS_EVENTS_BY_DEFAULT = True


def send(
    *args,
    handlers: Optional[List[Dict[str, str]]] = None,
    asynchronous: Optional[bool] = None,
    **kw
) -> None:
    """Send an event to the global ewoks event logger."""
    with _ewoks_event_logger(handlers=handlers, asynchronous=asynchronous) as logger:
        logger.info(*args, **kw)


def add_handler(
    handler,
    asynchronous: Optional[bool] = None,
) -> None:
    """Add a handler to the global ewoks event logger."""
    with _ewoks_event_logger() as logger:
        if _has_handler_instance(logger, handler):
            return
        if asynchronous is None and is_ewoks_event_handler(handler):
            asynchronous = handler.BLOCKING
        if asynchronous:
            handler = AsyncHandlerWrapper(handler)
        logger.addHandler(handler)


def remove_handler(handler: logging.Handler) -> None:
    """Remove a handler from all loggers that receive ewoks event."""
    with _ewoks_event_logger() as logger:
        for linstance, hinstance in _iter_handler_owners(logger, handler):
            linstance.removeHandler(hinstance)
            hinstance.close()


def cleanup():
    """Pending events will be dropped"""
    logging._acquireLock()
    try:
        _cleanup_ewoks_event_logger()
    finally:
        logging._releaseLock()


def _after_fork_in_child():
    cleanup()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_after_fork_in_child)


@contextmanager
def _ewoks_event_logger(
    handlers: Optional[List[Dict[str, str]]] = None, asynchronous: Optional[bool] = None
) -> Iterable[logging.Logger]:
    """Initialize and yield the ewoks event logger"""
    # Issue with logging and forking:
    # https://pythonspeed.com/articles/python-multiprocessing/

    logging._acquireLock()
    try:
        if _ewoks_event_logger_requires_cleanup():
            _cleanup_ewoks_event_logger()
        if _ewoks_event_logger_requires_init():
            _init_ewoks_event_logger(handlers, asynchronous)
        yield logging.getLogger(EWOKS_EVENT_LOGGER_NAME)
    finally:
        logging._releaseLock()


def _cleanup_ewoks_event_logger():
    """Cleanup and delete the global ewoks event logger"""
    cleanup_logger(EWOKS_EVENT_LOGGER_NAME)


def _ewoks_event_logger_requires_init() -> bool:
    logger = logging.getLogger(EWOKS_EVENT_LOGGER_NAME)
    return not hasattr(logger, "ewoks_pid")


def _ewoks_event_logger_requires_cleanup() -> bool:
    logger = logging.getLogger(EWOKS_EVENT_LOGGER_NAME)
    ewoks_pid = getattr(logger, "ewoks_pid", None)
    return ewoks_pid is not None and ewoks_pid != os.getpid()


def _init_ewoks_event_logger(
    handlers: Optional[List[Dict[str, str]]], asynchronous: Optional[bool]
):
    logger = logging.getLogger(EWOKS_EVENT_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.ewoks_pid = os.getpid()
    if not handlers:
        return
    for desc in handlers:
        try:
            kwargs = {
                arg["name"]: arg["value"] for arg in desc.get("arguments", list())
            }
            handler = instantiate_handler(desc["class"], **kwargs)
        except Exception as e:
            raise RuntimeError(
                "cannot create an ewoks event handler from the description"
            ) from e
        asynchronous_handler = desc.get("asynchronous", asynchronous)
        add_handler(handler, asynchronous=asynchronous_handler)


def _iter_loggers(logger: logging.Logger) -> Iterable[logging.Logger]:
    """Yield all loggers which will receive ewoks events."""
    _logger = logger
    while _logger is not None:
        yield _logger
        if not _logger.propagate:
            return
        _logger = _logger.parent


def _iter_handler_owners(
    logger: logging.Logger, instance: logging.Handler
) -> Iterable[Tuple[logging.Logger, logging.Handler]]:
    """Yield all loggers which have a specific handler (or a handler that wraps the specific event handler)."""
    for _logger in _iter_loggers(logger):
        for handler in _logger.handlers:
            if handler is instance:
                yield _logger, instance
            elif isinstance(handler, AsyncHandlerWrapper):
                instance2 = handler.wrapped_handler
                if instance2 is instance:
                    yield _logger, instance2


def _has_handler_instance(logger: logging.Logger, instance: logging.Handler) -> bool:
    """Is this handler registered with a logger or it's parents?"""
    for _ in _iter_handler_owners(logger, instance):
        return True
    return False
