from collections.abc import Mapping
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from . import bindings
from .engine_interface import Path
from .engine_interface import RawExecInfoType
from .engine_interface import TaskGraph
from .engine_interface import WorkflowEngineWithSerialization
from .node import NodeIdType
from .task import Task


class CoreWorkflowEngine(WorkflowEngineWithSerialization):

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

    def deserialize_graph(
        self,
        graph: Any,
        *,
        inputs: Optional[List[dict]] = None,
        representation: Optional[str] = None,
        root_dir: Optional[Union[str, Path]] = None,
        root_module: Optional[str] = None,
        # Serializer specific:
        **load_options,
    ) -> TaskGraph:
        return bindings.load_graph(
            graph,
            inputs=inputs,
            representation=representation,
            root_dir=root_dir,
            root_module=root_module,
            **load_options,
        )

    def serialize_graph(
        self,
        graph: TaskGraph,
        destination,
        *,
        representation: Optional[str] = None,
        # Serializer specific:
        **save_options,
    ) -> Union[str, dict]:
        return bindings.save_graph(
            graph, destination, representation=representation, **save_options
        )

    def get_graph_representation(self, graph: Any) -> Optional[str]:
        if isinstance(graph, Mapping):
            return "json_dict"
        if isinstance(graph, (str, Path)):
            if graph == "test_core":
                return "test_core"
            if isinstance(graph, str) and "{" in graph and "}" in graph:
                return "json_string"
            filename = str(graph).lower()
            if filename.endswith(".json"):
                return "json"
            elif filename.endswith((".yml", ".yaml")):
                return "yaml"
