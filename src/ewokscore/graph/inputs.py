import inspect
import logging
import textwrap
from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Type

import networkx
from ewoksutils import import_utils

from ..dynamictask import get_dynamically_task_class
from ..missing_data import MISSING_DATA
from ..missing_data import is_missing_data
from ..model import BaseInputModel
from ..node import NodeIdType
from ..task import Task
from .taskgraph import TaskGraph

_logger = logging.getLogger(__name__)


@dataclass
class NodeInput:
    id: NodeIdType
    label: Optional[str]
    task_identifier: str
    name: str
    value: Any
    required: bool
    description: Optional[str]
    examples: Optional[List[Any]]
    import_error: Optional[Exception]

    @property
    def has_value(self) -> bool:
        return not is_missing_data(self.value)

    @property
    def required_without_value(self) -> bool:
        return self.required and not self.has_value


def graph_inputs(graph: TaskGraph) -> List[NodeInput]:
    """
    Return a list of workflow inputs. These are all the task
    inputs that are not connected to task outputs from previous
    nodes in the workflow.
    """
    node_inputs = _get_node_inputs(graph.graph)

    task_identifiers = set(node_input.task_identifier for node_input in node_inputs)
    short_task_ids = _shorten_task_identifiers(task_identifiers)
    for node_input in node_inputs:
        node_input.task_identifier = short_task_ids[node_input.task_identifier]

    return node_inputs


def graph_inputs_as_table(
    graph: TaskGraph, column_widths: Optional[Dict[str, Optional[int]]] = None
) -> Tuple[List[str], List[List[str]], Dict[str, str], List[str]]:
    """
    Return table of workflow input parameters.
    """
    node_inputs = graph_inputs(graph)
    column_names, rows, footnotes = _graph_inputs_to_table(
        node_inputs, column_widths=column_widths
    )
    metadata = {}
    if graph.graph_id:
        metadata["id"] = graph.graph_id
    if graph.graph_label:
        metadata["description"] = graph.graph_label
    return column_names, rows, metadata, footnotes


def _graph_inputs_to_table(
    node_inputs: List[NodeInput],
    column_widths: Optional[Dict[str, Optional[int]]] = None,
) -> Tuple[List[str], List[List[str]], List[str]]:
    """
    Convert a list of workflow inputs to a table with string values.
    """
    if column_widths is None:
        column_widths = {
            "name": None,
            "value": 30,
            "description": 40,
            "examples": 30,
            "task_identifier": None,
            "id": None,
            "label": None,
        }

    # Column names
    column_names = [s.replace("_", " ").capitalize() for s in column_widths]

    # Highlight required inputs without a value
    highlighted = [
        node_input for node_input in node_inputs if node_input.required_without_value
    ]
    node_inputs = highlighted + [
        node_input
        for node_input in node_inputs
        if not node_input.required_without_value
    ]

    # Generate table
    rows = []
    has_import_error = False
    for node_input in node_inputs:
        row = []
        for column_name, width in column_widths.items():
            value = _get_row_value(node_input, column_name)
            str_val = _row_value_as_string(value, width)
            row.append(str_val)
        rows.append(row)

    # Remove empty columns
    columns = list(zip(*rows))
    non_empty_column_indices = [
        i for i, col in enumerate(columns) if any(cell.strip() for cell in col)
    ]
    column_names = [column_names[i] for i in non_empty_column_indices]
    rows = [[row[i] for i in non_empty_column_indices] for row in rows]

    # Footnotes
    footnotes = []
    has_required_without_value = any(
        node_input.required_without_value for node_input in node_inputs
    )
    if has_required_without_value:
        footnotes = ["⁽*⁾ Value is required for execution."]
    has_import_error = any(node_input.import_error for node_input in node_inputs)
    if has_import_error:
        footnotes.append(
            "⁽†⁾ Information from workflow only (task cannot be imported)."
        )

    return column_names, rows, footnotes


def _get_row_value(node_input: NodeInput, column_name: str) -> Any:
    value = getattr(node_input, column_name)
    if column_name == "name":
        if node_input.required_without_value:
            return f"{value}⁽*⁾"
        if node_input.import_error:
            return f"{value}⁽†⁾"
    if column_name == "value":
        return repr(value)
    if column_name == "examples" and value:
        return list(map(repr, value))
    return value


def _row_value_as_string(value: Any, width: Optional[int]) -> str:
    if value is None:
        str_val = ""
    elif isinstance(value, str):
        str_val = value
    elif isinstance(value, list):
        if width:
            str_val = _wrap_bullet_list(value, width)
            width = None
        else:
            str_val = "• " + "\n• ".join(value)
    else:
        str_val = str(value)

    if width:
        return "\n".join(textwrap.wrap(str_val, width=width))
    return str_val


def _wrap_bullet_list(items: List[str], width: int) -> str:
    wrapper = textwrap.TextWrapper(
        width=width, initial_indent="• ", subsequent_indent="  "
    )
    return "\n".join(wrapper.fill(str(item)) for item in items)


def _get_node_inputs(graph: networkx.DiGraph) -> List[NodeInput]:
    """
    Return all the task inputs that are not connected to task
    outputs from previous nodes in the workflow.
    """
    all_node_inputs = []
    for node_id, node_attrs in graph.nodes.items():
        node_inputs = _get_all_node_inputs(node_id, node_attrs)
        connected_input_names = _get_connected_input_names(graph, node_id)
        all_node_inputs += [
            node_input
            for node_input in node_inputs
            if node_input.name not in connected_input_names
        ]
    return all_node_inputs


def _get_connected_input_names(
    graph: networkx.DiGraph, node_id: NodeIdType
) -> Set[str]:
    """
    Return all input parameter names that are connected to an output from a previous task.
    """
    connected_input_names = set()
    for predecessor_id in graph.predecessors(node_id):
        link_attrs = graph.get_edge_data(predecessor_id, node_id)

        if not link_attrs:
            continue

        data_mappings = link_attrs.get("data_mapping", [])
        for mapping in data_mappings:
            target_input = mapping.get("target_input")
            if target_input:
                connected_input_names.add(target_input)

        map_all_data = link_attrs.get("map_all_data", False)
        if map_all_data:
            node_attrs = graph.nodes[predecessor_id]
            task_type = node_attrs["task_type"]
            task_identifier = node_attrs["task_identifier"]
            output_names = _get_all_task_output_names(task_type, task_identifier)
            connected_input_names.update(output_names)
    return connected_input_names


def _get_all_node_inputs(
    node_id: NodeIdType, node_attrs: Dict[str, Any]
) -> List[NodeInput]:
    """
    Return all the input parameters of a node.
    """
    task_type = node_attrs["task_type"]
    task_identifier = node_attrs["task_identifier"]
    default_inputs = node_attrs.get("default_inputs", [])
    default_input_map = {item["name"]: item.get("value") for item in default_inputs}

    node_attrs = {
        "id": node_id,
        "label": node_attrs.get("label", None),
        "task_identifier": task_identifier,
    }

    if task_type == "class":
        try:
            task_cls = import_utils.import_qualname(task_identifier)
        except Exception as import_error:
            _logger.warning(f"Cannot import {task_identifier!r}: {import_error}")
            node_input_iterator = _node_inputs_from_defaults(
                default_input_map, node_attrs, import_error
            )
        else:
            node_input_iterator = _node_inputs_from_class(
                task_cls, default_input_map, node_attrs
            )
    elif task_type == "generated":
        try:
            task_cls = get_dynamically_task_class(
                node_attrs.get("task_generator"), task_identifier
            )
        except Exception as import_error:
            _logger.warning(f"Cannot import {task_identifier!r}: {import_error}")
            node_input_iterator = _node_inputs_from_defaults(
                default_input_map, node_attrs, import_error
            )
        else:
            node_input_iterator = _node_inputs_from_class(
                task_cls, default_input_map, node_attrs
            )
    elif task_type in ("method", "ppfmethod"):
        try:
            task_method = import_utils.import_qualname(task_identifier)
        except Exception as import_error:
            _logger.warning(f"Cannot import {task_identifier!r}: {import_error}")
            node_input_iterator = _node_inputs_from_defaults(
                default_input_map, node_attrs, import_error
            )
        else:
            node_input_iterator = _node_inputs_from_method(
                task_method, default_input_map, node_attrs
            )
    else:
        _logger.warning(
            f"Task type {task_type!r} is not supported ({task_identifier!r}). Only using default values from the workflow."
        )
        import_error = TypeError(f"Cannot get inputs from task type {task_type!r}")
        node_input_iterator = _node_inputs_from_defaults(
            default_input_map, node_attrs, import_error
        )

    return list(node_input_iterator)


def _get_all_task_output_names(task_type: str, task_identifier: str) -> List[str]:
    """
    Return all the output parameter names of a task.
    """
    if task_type == "class":
        try:
            task_cls = import_utils.import_qualname(task_identifier)
        except Exception:
            return []
        else:
            return _task_output_names_from_class(task_cls)
    elif task_type == "method":
        return ["return_value"]
    else:
        return []


def _node_inputs_from_class(
    task_cls: Type[Task], default_input_map: Dict[str, Any], node_attrs: Dict[str, Any]
) -> Generator[NodeInput, None, None]:
    """
    Return all task input parameters based on a task class.
    """
    input_model = task_cls.input_model()
    if input_model:
        yield from _node_inputs_from_class_model(
            input_model, default_input_map, node_attrs
        )
    else:
        yield from _node_inputs_from_class_methods(
            task_cls, default_input_map, node_attrs
        )


def _node_inputs_from_class_model(
    input_model: BaseInputModel,
    default_input_map: Dict[str, Any],
    node_attrs: Dict[str, Any],
) -> Generator[NodeInput, None, None]:
    """
    Return all task input parameters based on an input model.
    """
    for name, field in input_model.model_fields.items():
        required = field.is_required()

        if name in default_input_map:
            # Default input overwrites model default (if any)
            value = default_input_map[name]
        else:
            try:
                default = field.get_default()
            except Exception:
                # Field has no default value
                value = MISSING_DATA
            else:
                # Field has a default value
                value = default

        yield NodeInput(
            **node_attrs,
            name=name,
            required=required,
            value=value,
            description=field.description,
            examples=field.examples,
            import_error=None,
        )


def _node_inputs_from_class_methods(
    task_cls: Type[Task], default_input_map: Dict[str, Any], node_attrs: Dict[str, Any]
) -> Generator[NodeInput, None, None]:
    """
    Return all task input parameters based on a task class.
    """
    input_names = [(name, True) for name in sorted(task_cls.required_input_names())]
    input_names += [(name, False) for name in sorted(task_cls.optional_input_names())]

    for name, required in input_names:
        value = default_input_map.get(name, MISSING_DATA)
        yield NodeInput(
            **node_attrs,
            name=name,
            required=required,
            value=value,
            description=None,
            examples=None,
            import_error=None,
        )


def _node_inputs_from_method(
    task_method: Callable, default_input_map: Dict[str, Any], node_attrs: Dict[str, Any]
) -> Generator[NodeInput, None, None]:
    """
    Return all task input parameters based on a task method.
    """
    sig = inspect.signature(task_method)
    for name, param in sig.parameters.items():
        if param.kind in (param.kind.VAR_POSITIONAL, param.kind.VAR_KEYWORD):
            continue

        required = param.default is inspect.Parameter.empty
        if name in default_input_map:
            # Default input overwrites parameter default (if any)
            value = default_input_map[name]
        elif required:
            # Parameter has no default value
            value = MISSING_DATA
        else:
            # Parameter has a default value
            value = param.default

        yield NodeInput(
            **node_attrs,
            name=name,
            required=required,
            value=value,
            description=None,
            examples=None,
            import_error=None,
        )


def _task_output_names_from_class(task_cls) -> List[str]:
    return sorted(task_cls.output_names())


def _node_inputs_from_defaults(
    default_input_map: Dict[str, Any],
    node_attrs: Dict[str, Any],
    import_error: Exception,
) -> Generator[NodeInput, None, None]:
    for name, value in default_input_map.items():
        yield NodeInput(
            **node_attrs,
            name=name,
            required=True,
            value=value,
            description=None,
            examples=None,
            import_error=import_error,
        )


def _shorten_task_identifiers(task_identifiers: Sequence[str]) -> Dict[str, str]:
    """
    Return a mapping from full task identifiers to the shortest unique suffixes.
    """
    task_identifiers = set(task_identifiers)
    nunique = len(task_identifiers)

    all_reversed_parts = {
        tid: tuple(reversed(tid.split("."))) for tid in task_identifiers
    }
    reversed_parts = {
        tid: (tid_parts[0],) for tid, tid_parts in all_reversed_parts.items()
    }

    while True:
        all_parts = list(reversed_parts.values())
        nunique_current = len(set(all_parts))
        if nunique_current == nunique:
            break
        for tid, tid_parts in list(reversed_parts.items()):
            if all_parts.count(tid_parts) == 1:
                continue
            i = len(tid_parts)
            full_tid_parts = all_reversed_parts[tid]
            if i < len(full_tid_parts):
                reversed_parts[tid] = reversed_parts[tid] + (full_tid_parts[i],)

    return {pid: ".".join(reversed(parts)) for pid, parts in reversed_parts.items()}
