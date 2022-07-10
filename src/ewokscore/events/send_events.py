"""Define and parse ewoks events
"""

from numbers import Number
from typing import Dict, List, Mapping, Optional
from datetime import datetime
import traceback
from ewoksutils.event_utils import FIELD_TYPES

from . import global_state
from .initialize_events import ExecInfoType


def send_job_event(**kw):
    kw = _preprocess_event(**kw)
    logargs, logkwargs = _parse_job_event(**kw)
    _send_event(*logargs, **logkwargs)


def send_workflow_event(**kw):
    kw = _preprocess_event(**kw)
    logargs, logkwargs = _parse_workflow_event(**kw)
    _send_event(*logargs, **logkwargs)


def send_task_event(**kw):
    kw = _preprocess_event(**kw)
    logargs, logkwargs = _parse_task_event(**kw)
    _send_event(*logargs, **logkwargs)


def timestamp() -> str:
    return datetime.now().astimezone().isoformat()


def _preprocess_event(execinfo: ExecInfoType = None, **logkwargs):
    if execinfo:
        logkwargs = {**execinfo, **logkwargs}
    if not logkwargs.get("time"):
        logkwargs["time"] = timestamp()
    _parse_exception(logkwargs)
    return logkwargs


def _parse_exception(logkwargs):
    exception = logkwargs.pop("exception", None)
    if exception is None:
        return
    elif isinstance(exception, str):
        logkwargs["error"] = True
        tb = exception
        error_message = _extract_reason_from_traceback(tb)
        if not logkwargs.get("error_message"):
            logkwargs["error_message"] = error_message
        if not logkwargs.get("error_traceback"):
            logkwargs["error_traceback"] = tb
    elif isinstance(exception, BaseException):
        logkwargs["error"] = True
        tb = "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )
        if not logkwargs.get("error_traceback"):
            logkwargs["error_traceback"] = tb
        if logkwargs.get("context") == "node":
            exception = _first_exception(exception)
        if not logkwargs.get("error_message"):
            error_message = str(exception)
            if not error_message:
                error_message = type(exception).__name__
            logkwargs["error_message"] = error_message
    else:
        raise TypeError(
            "ewoks event field 'exception' should be a string or an exception instance"
        )


def _first_exception(exception: BaseException) -> BaseException:
    while True:
        if exception.__cause__ is not None:
            # exception raised from another exception
            exception = exception.__cause__
        elif exception.__context__ is not None:
            # exception raised during handling of another exception
            exception = exception.__context__
        else:
            return exception


def _extract_reason_from_traceback(tb: str) -> str:
    for line in reversed(tb.split("\n")):
        if ":" in line:
            return line
    return ""


def _parse_workflow_event(**logkwargs):
    event_data, logkwargs = _extract_workflow_fields(**logkwargs)
    msg = _validate_event(event_data)
    logargs = (
        "[job %r] [workflow %r] %s",
        event_data["job_id"],
        event_data["workflow_id"],
        msg,
    )
    logkwargs["event_data"] = event_data
    return logargs, logkwargs


def _parse_job_event(**logkwargs):
    event_data, logkwargs = _extract_job_fields(**logkwargs)
    msg = _validate_event(event_data)
    logargs = ("[job %r] %s", event_data["job_id"], msg)
    logkwargs["event_data"] = event_data
    return logargs, logkwargs


def _parse_task_event(**logkwargs):
    event_data, logkwargs = _extract_task_fields(**logkwargs)
    msg = _validate_event(event_data)
    logargs = (
        "[job %r] [workflow %r] [node %r] [task %r] %s",
        event_data["job_id"],
        event_data["workflow_id"],
        event_data["node_id"],
        event_data["task_id"],
        msg,
    )
    logkwargs["event_data"] = event_data
    return logargs, logkwargs


def _extract_common_fields(
    host_name: str,
    process_id: int,
    user_name: str,
    job_id: str,
    event: str,
    binding: Optional[str] = None,
    time: Optional[str] = None,
    error: Optional[bool] = None,
    error_message: Optional[str] = None,
    error_traceback: Optional[str] = None,
    **logkwargs,
):
    event_data = {
        "host_name": host_name,
        "process_id": process_id,
        "user_name": user_name,
        "job_id": job_id,
        "binding": binding,
        "type": event,
        "time": time,
        "error": error,
        "error_message": error_message,
        "error_traceback": error_traceback,
    }
    return event_data, logkwargs


def _extract_job_fields(
    **logkwargs,
):
    event_data, logkwargs = _extract_common_fields(**logkwargs)
    event_data["context"] = "job"
    return event_data, logkwargs


def _extract_workflow_fields(
    workflow_id: str,
    **logkwargs,
):
    event_data, logkwargs = _extract_job_fields(**logkwargs)
    event_data["context"] = "workflow"
    event_data["workflow_id"] = workflow_id
    return event_data, logkwargs


def _extract_task_fields(
    node_id: str,
    task_id: str,
    progress: Optional[Number] = None,
    task_uri: Optional[str] = None,
    input_uris: Optional[List[Dict[str, Optional[str]]]] = None,
    output_uris: Optional[List[Dict[str, Optional[str]]]] = None,
    **logkwargs,
):
    event_data, logkwargs = _extract_workflow_fields(**logkwargs)
    event_data["context"] = "node"
    event_data["node_id"] = node_id
    event_data["task_id"] = task_id
    event_data["progress"] = progress
    event_data["task_uri"] = task_uri
    event_data["input_uris"] = input_uris
    event_data["output_uris"] = output_uris
    return event_data, logkwargs


def _validate_event(event_data: dict) -> str:
    event_data.update((field, None) for field in set(FIELD_TYPES) - set(event_data))
    event = event_data["type"]
    if event_data["context"] == "job":
        obj = "job"
    elif event_data["context"] == "workflow":
        obj = "workflow"
    elif event_data["context"] == "node":
        obj = "task"
    else:
        raise ValueError(f"context '{event_data['context']}' is unknown")
    if event == "start":
        return f"{obj} started"
    elif event == "end":
        error = bool(
            event_data["error"]
            or event_data["error_message"]
            or event_data["error_traceback"]
        )
        event_data["error"] = error
        if error:
            if event_data["error_message"] is None:
                event_data["error_message"] = ""
            if event_data["error_traceback"] is None:
                event_data["error_traceback"] = ""
        if not error:
            return f"{obj} finished"
        elif event_data["error"] and event_data["error_message"]:
            return f"{obj} failed ({event_data['error_message']})"
        else:
            return f"{obj} failed"
    elif event == "progress":
        if not isinstance(event_data["progress"], Number):
            event_data["progress"] = float("nan")
        return f"{obj} progress {event_data['progress']}%"
    else:
        raise ValueError(f"unknown ewoks event type '{event}'")


def _send_event(msg: str, *args, event_data=None, extra=None, contexts=None, **kw):
    if not isinstance(event_data, Mapping):
        raise TypeError("'event_data' should be a mapping")
    if extra:
        if not isinstance(extra, Mapping):
            raise TypeError("'extra' should be a mapping")
        extra = {**extra, **event_data}
    else:
        extra = event_data
    global_state.send(msg, *args, extra=extra, **kw)
