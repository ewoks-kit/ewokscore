"""Initialize ewoks event fields"""

import getpass
import os
import socket
from typing import Mapping
from typing import Optional
from typing import Union
from uuid import uuid4

import networkx

ExecInfoType = Union[Mapping, None]


def init_job(execinfo: ExecInfoType, **static_job_info) -> ExecInfoType:
    if execinfo is None:
        return None
    execinfo = dict(execinfo)
    set_environment(execinfo)
    job_id = execinfo.get("job_id")
    if job_id is None:
        execinfo["job_id"] = str(uuid4())
    execinfo.update(static_job_info)
    return execinfo


def init_workflow(
    execinfo: ExecInfoType,
    workflow: Union[networkx.DiGraph, str, None] = None,
    **static_workflow_info,
) -> ExecInfoType:
    if execinfo is None:
        return None
    execinfo = dict(execinfo)
    set_environment(execinfo)
    if workflow is None:
        default = (
            f"{execinfo['host_name']}-{execinfo['process_id']}-{execinfo['user_name']}"
        )
        execinfo["workflow_id"] = default
    elif isinstance(workflow, str):
        execinfo["workflow_id"] = workflow
    else:
        try:
            execinfo["workflow_id"] = str(workflow.graph["id"])
        except KeyError:
            raise ValueError("the graph needs an 'id' for execution events")
    execinfo.update(static_workflow_info)
    return execinfo


def init_node(
    execinfo: ExecInfoType, node_id: Optional[str], task_id: Optional[str]
) -> ExecInfoType:
    if execinfo is None:
        return None
    execinfo = dict(execinfo)
    set_environment(execinfo)
    if node_id:
        execinfo["node_id"] = node_id
    if task_id:
        execinfo["task_id"] = task_id
    return execinfo


def set_environment(execinfo: ExecInfoType) -> ExecInfoType:
    if execinfo is None:
        return None
    execinfo["host_name"] = socket.gethostname()
    execinfo["process_id"] = os.getpid()
    execinfo["user_name"] = getpass.getuser()
