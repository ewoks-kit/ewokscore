from typing import Any, Optional, List, Union, Dict

from . import bindings
from .task import Task
from .node import NodeIdType
from .events.contexts import RawExecInfoType
from .engine_interface import WorkflowEngine


class CoreWorkflowEngine(WorkflowEngine):

    def execute_graph(
        self,
        graph: Any,
        *,
        inputs: Optional[List[dict]] = None,
        load_options: Optional[dict] = None,
        varinfo: Optional[dict] = None,
        execinfo: RawExecInfoType = None,
        task_options: Optional[dict] = None,
        outputs: Optional[List[dict]] = None,
        merge_outputs: Optional[bool] = True,
        # Engine specific:
        output_tasks: Optional[bool] = False,
        raise_on_error: Optional[bool] = True,
    ) -> Union[Dict[NodeIdType, Task], Dict[str, Any]]:
        return bindings.execute_graph(
            graph,
            inputs=inputs,
            load_options=load_options,
            varinfo=varinfo,
            execinfo=execinfo,
            task_options=task_options,
            raise_on_error=raise_on_error,
            outputs=outputs,
            merge_outputs=merge_outputs,
            output_tasks=output_tasks,
        )
