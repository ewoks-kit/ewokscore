import textwrap
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple

import networkx

from ..node_signature import node_signature
from .models import GraphInput
from .models import NodeIdType
from .taskgraph import TaskGraph


def graph_inputs(graph: TaskGraph) -> List[GraphInput]:
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
    node_inputs: List[GraphInput],
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


def _get_row_value(node_input: GraphInput, column_name: str) -> Any:
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


def _get_node_inputs(graph: networkx.DiGraph) -> List[GraphInput]:
    """
    Return all the task inputs that are not connected to task
    outputs from previous nodes in the workflow.
    """
    all_node_inputs = []
    for node_id, node_attrs in graph.nodes.items():
        signature = node_signature(node_id, node_attrs)
        connected_input_names = _get_connected_input_names(graph, node_id)
        all_node_inputs += [
            GraphInput(
                id=signature.id,
                label=signature.label,
                task_identifier=signature.task_identifier,
                name=node_input.name,
                value=node_input.value,
                required=node_input.required,
                description=node_input.description,
                examples=node_input.examples,
                import_error=signature.import_error,
            )
            for node_input in signature.inputs
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
            signature = node_signature(
                predecessor_id, node_attrs=graph.nodes[predecessor_id]
            )
            connected_input_names.update([output.name for output in signature.outputs])
    return connected_input_names


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
