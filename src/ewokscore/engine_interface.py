from pathlib import Path
from abc import ABC, abstractmethod
from typing import Any, Optional, Union, List

from . import bindings
from .graph import TaskGraph
from .events.contexts import RawExecInfoType
from .graph.serialize import GraphRepresentation


class WorkflowEngine(ABC):
    """Python projects that provide Ewoks engines for loading, saving and executing
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
        graph: Any,
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

    def load_graph(
        self,
        graph: Any,
        *,
        inputs: Optional[List[dict]] = None,
        representation: Optional[Union[GraphRepresentation, str]] = None,
        root_dir: Optional[Union[str, Path]] = None,
        root_module: Optional[str] = None,
        # Graph representation specific:
        **load_options,
    ) -> TaskGraph:
        """Convert a computational graph representation to the canonical in-memory representation `TaskGraph`."""
        return bindings.load_graph(
            graph,
            inputs=inputs,
            representation=representation,
            root_dir=root_dir,
            root_module=root_module,
            **load_options,
        )

    def save_graph(
        self,
        graph: TaskGraph,
        destination,
        *,
        representation: Optional[Union[GraphRepresentation, str]] = None,
        # Graph representation specific:
        **save_options,
    ) -> Union[str, dict]:
        """Convert the canonical computational graph representation `TaskGraph` to another representation."""
        return bindings.save_graph(
            graph, destination, representation=representation, **save_options
        )

    def is_native_graph(
        self,
        graph: Any,
        *,
        representation: Optional[Union[GraphRepresentation, str]] = None,
    ) -> bool:
        """Return True if the given graph representation is specific to this engine."""
        return False
