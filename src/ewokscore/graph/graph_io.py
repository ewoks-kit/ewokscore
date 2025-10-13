from typing import Dict
from typing import Iterator
from typing import List
from typing import Mapping
from typing import Optional
from typing import Union

import networkx

from .. import missing_data
from ..node import NodeIdType
from ..node import get_node_label
from ..task import Task
from .analysis import end_nodes
from .analysis import start_nodes


def update_default_inputs(
    graph: networkx.DiGraph, inputs: Optional[List[dict]] = None
) -> None:
    """Input items have the following keys:

    - name: input variable name
    - value: input variable value
    - id (optional): node id
    - label (optional): used when `id` is missing
    - task_identifier (optional): used when `id` is missing
    - all (optional): used when `id`, `label` and `task_identifier` are missing (`True`: all nodes, `False`: start nodes)
    """
    inputs = parse_inputs(graph, inputs)
    keys_to_update = "name", "value"
    for input_item in inputs:
        node_id = input_item.get("id")
        if node_id is None:
            continue
        node_attrs = graph.nodes[node_id]
        default_inputs = node_attrs.get("default_inputs")
        input_item = {k: input_item[k] for k in keys_to_update}
        if default_inputs:
            for existing_input_item in default_inputs:
                if existing_input_item["name"] == input_item["name"]:
                    existing_input_item.update(input_item)
                    break
            else:
                default_inputs.append(input_item)
        else:
            node_attrs["default_inputs"] = [input_item]


def parse_inputs(
    graph: networkx.DiGraph, inputs: Optional[List[dict]] = None
) -> List[dict]:
    """Input items have the following keys:

    - name: input variable name
    - value: input variable value
    - id (optional): node id
    - label (optional): used when `id` is missing
    - task_identifier (optional): used when `id` is missing
    - all (optional): used when `id`, `label` and `task_identifier` are missing (`True`: all nodes, `False`: start nodes)
    """
    if not inputs:
        return list()
    required = {"name", "value"}
    returned = {"id", "name", "value"}
    parsed = list()
    for input_item in list(inputs):
        missing = required - input_item.keys()
        if missing:
            raise ValueError(f"missing keys in one of the graph inputs: {missing}")
        if "id" in input_item:
            parsed.append({k: v for k, v in input_item.items() if k in returned})
            continue

        node_filters = dict()
        for k in ("label", "task_identifier"):
            if k in input_item:
                node_filters[k] = input_item[k]

        if node_filters:
            node_ids = iter_node_ids(graph, **node_filters)
        elif input_item.get("all"):
            node_ids = graph.nodes
        else:
            node_ids = start_nodes(graph)

        for node_id in node_ids:
            input_item = {k: v for k, v in input_item.items() if k in returned}
            input_item["id"] = node_id
            parsed.append(input_item)
    return parsed


def parse_outputs(
    graph: networkx.DiGraph, outputs: Optional[List[dict]] = None
) -> List[dict]:
    """Output items have the following keys:

    - name (optional): output variable name (all outputs when missing)
    - new_name (optional): optional renaming when `name` is defined
    - id (optional): node id
    - label (optional): used when `id` is missing
    - task_identifier (optional): used when `id` is missing
    - all (optional): used when `id`, `label` and `task_identifier` are missing (`True`: all nodes, `False`: end nodes)
    """
    if outputs is None:
        outputs = [{"all": False}]
    parsed = list()
    returned = {"id", "name", "new_name"}
    for output_item in outputs:
        if "id" in output_item:
            parsed.append({k: v for k, v in output_item.items() if k in returned})
            continue

        node_filters = dict()
        for k in ("label", "task_identifier"):
            if k in output_item:
                node_filters[k] = output_item[k]

        if node_filters:
            node_ids = iter_node_ids(graph, **node_filters)
        elif output_item.get("all"):
            node_ids = graph.nodes
        else:
            node_ids = end_nodes(graph)

        for node_id in node_ids:
            output_item = {k: v for k, v in output_item.items() if k in returned}
            output_item["id"] = node_id
            parsed.append(output_item)

    return parsed


def iter_node_ids(
    graph: networkx.DiGraph,
    label: Optional[str] = None,
    task_identifier: Optional[str] = None,
) -> Iterator[NodeIdType]:
    """Yield nodes with matching `label` AND `task_identifier`"""
    for node_id, node_attrs in graph.nodes.items():
        return_id = False
        if label is not None:
            node_label = get_node_label(node_id, node_attrs)
            if label != node_label:
                continue
            return_id = True
        if task_identifier is not None:
            s = node_attrs.get("task_identifier")
            if not s or not s.endswith(task_identifier):
                continue
            return_id = True
        if return_id:
            yield node_id


def extract_output_values(
    node_id: NodeIdType, task_or_outputs: Union[Task, Mapping], outputs: List[dict]
) -> Optional[dict]:
    """Output items have the following keys:

    - id: node id
    - label (optional): used when `id` is missing
    - name (optional): output variable name (all outputs when missing)
    - new_name (optional): optional renaming when name is defined
    """
    output_values = None
    if isinstance(task_or_outputs, Task):
        task_output_values = None
    else:
        task_output_values = task_or_outputs
    for output_item in outputs:
        if output_item.get("id") != node_id:
            continue
        if task_output_values is None:
            task_output_values = task_or_outputs.get_output_values()
        if output_values is None:
            output_values = dict()
        name = output_item.get("name")
        if name:
            new_name = output_item.get("new_name", name)
            output_values[new_name] = task_output_values.get(
                name, missing_data.MISSING_DATA
            )
        else:
            output_values.update(task_output_values)
    return output_values


def add_output_values(
    output_values: dict,
    node_id: NodeIdType,
    task_or_outputs: Union[Task, Dict],
    outputs: List[dict],
    merge_outputs: Optional[bool] = True,
) -> None:
    """Output items have the following keys:

    - id: node id
    - label (optional): used when `id` is missing
    - name (optional): output variable name (all outputs when missing)
    - new_name (optional): optional renaming when name is defined
    """
    task_output_values = extract_output_values(node_id, task_or_outputs, outputs)
    if task_output_values is not None:
        if merge_outputs:
            output_values.update(task_output_values)
        else:
            output_values[node_id] = task_output_values
