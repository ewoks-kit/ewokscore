"""Manage the EWOKS event logger which is a global object"""

import logging
import os
from contextlib import contextmanager
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple

from ewoksutils.logging_utils.asyncwrapper import AsyncHandlerWrapper
from ewoksutils.logging_utils.cleanup import cleanup_handler
from ewoksutils.logging_utils.cleanup import cleanup_logger
from ewoksutils.logging_utils.cleanup import protect_logging_state

from .handlers import instantiate_handler
from .handlers import is_ewoks_event_handler

_app_logger = logging.getLogger(__name__)
EWOKS_EVENT_LOGGER_NAME = f"__{__name__}__"
ENABLE_EWOKS_EVENTS_BY_DEFAULT = True


def send(
    *args,
    handlers: Optional[List[Dict[str, Any]]] = None,
    asynchronous: Optional[bool] = None,
    **kw,
) -> None:
    """Log an EWOKS event with the EWOKS event handlers and the application handlers."""
    with _ewoks_event_logger(
        handlers=handlers, asynchronous=asynchronous, cleanup_on_different_handlers=True
    ) as logger:
        # Send to the EWOKS event handlers
        logger.info(*args, **kw)
        # Send to the application log handlers
        _app_logger.info(*args, **kw)


def add_handler(
    handler: logging.Handler,
    asynchronous: Optional[bool] = None,
) -> None:
    """Add a handler to the global EWOKS event logger."""
    with _ewoks_event_logger() as logger:
        if _has_handler_instance(logger, handler):
            return
        if asynchronous is None and is_ewoks_event_handler(handler):
            asynchronous = handler.BLOCKING
        if asynchronous:
            handler = AsyncHandlerWrapper(handler)
        logger.addHandler(handler)


def remove_handler(handler: logging.Handler) -> None:
    """Remove a handler from all loggers that receive EWOKS events."""
    with _ewoks_event_logger() as logger:
        for linstance, hinstance in _iter_handler_owners(logger, handler):
            linstance.removeHandler(hinstance)
            cleanup_handler(hinstance)


def cleanup():
    """Pending events will be dropped"""
    with protect_logging_state():
        _cleanup_ewoks_event_logger()


def _after_fork_in_child():
    cleanup()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_after_fork_in_child)


@contextmanager
def _ewoks_event_logger(
    handlers: Optional[List[Dict[str, Any]]] = None,
    asynchronous: Optional[bool] = None,
    cleanup_on_different_handlers: bool = False,
) -> Iterator[logging.Logger]:
    """Initialize and yield the EWOKS event logger"""
    # Issue with logging and forking:
    # https://pythonspeed.com/articles/python-multiprocessing/

    with protect_logging_state():
        if _ewoks_event_logger_requires_cleanup(
            handlers=handlers,
            cleanup_on_different_handlers=cleanup_on_different_handlers,
        ):
            _cleanup_ewoks_event_logger()
        if _ewoks_event_logger_requires_init():
            _init_ewoks_event_logger(handlers, asynchronous)
        yield logging.getLogger(EWOKS_EVENT_LOGGER_NAME)


def _cleanup_ewoks_event_logger():
    """Cleanup and delete the global EWOKS event logger"""
    cleanup_logger(EWOKS_EVENT_LOGGER_NAME)


def _ewoks_event_logger_requires_init() -> bool:
    logger = logging.getLogger(EWOKS_EVENT_LOGGER_NAME)
    return not hasattr(logger, "ewoks_pid")


def _ewoks_event_logger_requires_cleanup(
    handlers: Optional[List[Dict[str, Any]]] = None,
    cleanup_on_different_handlers: bool = False,
) -> bool:
    logger = logging.getLogger(EWOKS_EVENT_LOGGER_NAME)

    ewoks_pid = getattr(logger, "ewoks_pid", None)
    if ewoks_pid is not None and ewoks_pid != os.getpid():
        # Process forked
        return True

    if cleanup_on_different_handlers:
        ewoks_handlers = getattr(logger, "ewoks_handlers", None)
        if ewoks_handlers != handlers:
            return True

    return False


def _init_ewoks_event_logger(
    handlers: Optional[List[Dict[str, Any]]], asynchronous: Optional[bool]
):
    logger = logging.getLogger(EWOKS_EVENT_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.ewoks_pid = os.getpid()
    logger.ewoks_handlers = handlers
    logger.propagate = False
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
                "cannot create an EWOKS event handler from the description"
            ) from e
        asynchronous_handler = desc.get("asynchronous", asynchronous)
        add_handler(handler, asynchronous=asynchronous_handler)


def _iter_loggers(logger: logging.Logger) -> Iterator[logging.Logger]:
    """Yield all loggers which will receive EWOKS events."""
    _logger = logger
    while _logger is not None:
        yield _logger
        if not _logger.propagate:
            return
        _logger = _logger.parent


def _iter_handler_owners(
    logger: logging.Logger, instance: logging.Handler
) -> Iterator[Tuple[logging.Logger, logging.Handler]]:
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
