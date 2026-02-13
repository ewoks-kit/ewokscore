"""Contexts for job, workflow or node events. Allows for initializing
event fields and sending start/end events.
"""

from contextlib import contextmanager
from functools import wraps
from typing import Mapping, Union
from .send_events import send_job_event
from .send_events import send_workflow_event
from .send_events import ExecInfoType
from .initialize_events import init_job
from .initialize_events import init_workflow
from .initialize_events import init_node
from . import global_state


RawExecInfoType = Union[Mapping, bool, str, None]


def job_decorator(**static_job_info):
    def _job_decorator(method):
        @wraps(method)
        def wrapper(*args, execinfo: RawExecInfoType = None, **kw):
            with job_context(execinfo, **static_job_info) as execinfo:
                return method(*args, execinfo=execinfo, **kw)

        return wrapper

    return _job_decorator


@contextmanager
def job_context(execinfo: RawExecInfoType, **static_job_info) -> ExecInfoType:
    if execinfo is None:
        execinfo = global_state.ENABLE_EWOKS_EVENTS_BY_DEFAULT

    if isinstance(execinfo, str):
        execinfo = {"job_id": execinfo}
    elif isinstance(execinfo, bool):
        if execinfo:
            execinfo = dict()
        else:
            execinfo = None
    elif execinfo is None:
        pass
    elif not isinstance(execinfo, Mapping):
        raise TypeError

    execinfo = init_job(execinfo, **static_job_info)
    if execinfo is None:
        yield None
    else:
        with _context(execinfo, "job", send_job_event, execinfo["job_id"]) as execinfo:
            yield execinfo


@contextmanager
def workflow_context(execinfo: ExecInfoType, **kw) -> ExecInfoType:
    execinfo = init_workflow(execinfo, **kw)
    if execinfo is None:
        yield None
    else:
        with _context(
            execinfo, "workflow", send_workflow_event, execinfo["workflow_id"]
        ) as execinfo:
            yield execinfo


@contextmanager
def node_context(execinfo: ExecInfoType, **kw) -> ExecInfoType:
    yield init_node(execinfo, **kw)


@contextmanager
def _context(
    execinfo: ExecInfoType, context, send_context_event, obj_id
) -> ExecInfoType:
    contexts = execinfo.get("contexts")
    if contexts is None:
        contexts = {"job": list(), "workflow": list()}
        execinfo["contexts"] = contexts
    obj_ids = contexts[context]
    first_context = obj_id not in obj_ids
    if first_context:
        send_context_event(execinfo=execinfo, event="start")
        obj_ids.append(obj_id)
    try:
        yield execinfo
    except BaseException as e:
        if not execinfo.get("exception"):
            execinfo["exception"] = e
        raise
    finally:
        if first_context:
            obj_ids.remove(obj_id)
            send_context_event(execinfo=execinfo, event="end")
