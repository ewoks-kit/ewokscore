from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import List
from typing import Optional
from typing import Union

from .events.contexts import RawExecInfoType
from .graph import TaskGraph


class WorkflowEngine(ABC):
    """Python projects that provide Ewoks engines for deserializing, serializing and executing
    computational Ewoks graphs can implement this interface.

    To make it discoverable it can be added as an entry-point the the project. For
    example in a `pyproject.toml` file:

    .. code-block: toml

        [project.entry-points."ewoks.engines"]
        "<engine-name>" = "<project-name>.engine:MyWorkflowEngine"
    """

    @abstractmethod
    def execute_graph(
        self,
        graph: TaskGraph,
        *,
        inputs: Optional[List[dict]] = None,
        load_options: Optional[dict] = None,
        varinfo: Optional[dict] = None,
        execinfo: Optional[RawExecInfoType] = None,
        task_options: Optional[dict] = None,
        outputs: Optional[List[dict]] = None,
        merge_outputs: Optional[bool] = True,
        # Engine specific:
        **execute_options,
    ) -> Optional[dict]:
        """Execute a computional Ewoks graph."""
        pass


class WorkflowEngineWithSerialization(WorkflowEngine):
    """Ewoks engines with graph serialization capabilities."""

    @abstractmethod
    def deserialize_graph(
        self,
        graph: Any,
        *,
        inputs: Optional[List[dict]] = None,
        representation: Optional[str] = None,
        root_dir: Optional[Union[str, Path]] = None,
        root_module: Optional[str] = None,
        # Serializer specific:
        **deserialize_options,
    ) -> TaskGraph:
        """Convert a computational graph representation to the canonical in-memory representation `TaskGraph`."""
        pass

    @abstractmethod
    def serialize_graph(
        self,
        graph: TaskGraph,
        destination: Any,
        *,
        representation: Optional[str] = None,
        # Serializer specific:
        **serialize_options,
    ) -> Any:
        """Convert the canonical computational graph representation `TaskGraph` to another representation."""
        pass

    @abstractmethod
    def get_graph_representation(self, graph: Any) -> Optional[str]:
        """Return the representation if the engine recognizes the graph object."""
        pass
