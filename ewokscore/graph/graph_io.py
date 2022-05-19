from typing import Dict, List, Mapping, Optional, Union
import networkx

from .analysis import start_nodes
from .analysis import end_nodes
from ..node import NodeIdType
from ..node import get_node_label
from .. import missing_data
from ..task import Task


def update_default_inputs(graph: networkx.DiGraph, default_inputs: List[dict]) -> None:
    """Input items have the following keys:
    * id: node id
    * label (optional): used when id is missing
    * name: input variable name
    * value: input variable value
    * all (optional): used when id and label is missing (True: all nodes, False: start nodes)
    """
    parse_default_inputs(graph, default_inputs)
    for input_item in default_inputs:
        node_id = input_item.get("id")
        if node_id is None:
            continue
        node_attrs = graph.nodes[node_id]
        existing_inputs = node_attrs.get("default_inputs")
        if existing_inputs:
            for existing_input_item in existing_inputs:
                if existing_input_item["name"] == input_item["name"]:
                    existing_input_item["value"] = input_item["value"]
                    break
            else:
                existing_inputs.append(input_item)
        else:
            node_attrs["default_inputs"] = [input_item]


def parse_default_inputs(graph: networkx.DiGraph, default_inputs: List[dict]) -> None:
    """Input items have the following keys:
    * id: node id
    * label (optional): used when id is missing
    * name: input variable name
    * value: input variable value
    * all (optional): used when id and label is missing (True: all nodes, False: start nodes)
    """
    extra = list()
    required = {"name", "value"}
    for input_item in default_inputs:
        missing = required - input_item.keys()
        if missing:
            raise ValueError(f"missing keys in one of the graph inputs: {missing}")
        if "id" in input_item:
            continue
        elif "label" in input_item:
            node_label = input_item["label"]
            node_id = get_node_id(graph, node_label)
            if node_id is None:
                raise ValueError(f"Node label '{node_label}' does not exist")
            input_item["id"] = node_id
        else:
            if input_item.get("all"):
                nodes = graph.nodes
            else:
                nodes = start_nodes(graph)
            for node_id in nodes:
                input_item = dict(input_item)
                input_item["id"] = node_id
                extra.append(input_item)
    default_inputs += extra


def parse_outputs(
    graph: networkx.DiGraph, outputs: Optional[List[dict]] = None
) -> None:
    """Output items have the following keys:
    * id: node id
    * label (optional): used when id is missing
    * name (optional): output variable name (all outputs when missing)
    * new_name (optional): optional renaming when name is defined
    * all (optional): used when id and label is missing (True: all nodes, False: end nodes)
    """
    if outputs is None:
        outputs = [{"all": False}]
    parsed = list()
    for output_item in outputs:
        if "id" in output_item:
            parsed.append(dict(output_item))
            continue
        elif "label" in output_item:
            node_label = output_item["label"]
            node_id = get_node_id(graph, node_label)
            if node_id is None:
                raise ValueError(f"Node label '{node_label}' does not exist")
            output_item = dict(output_item)
            output_item["id"] = node_id
            parsed.append(output_item)
        else:
            if output_item.get("all"):
                nodes = graph.nodes
            else:
                nodes = end_nodes(graph)
            output_item = dict(output_item)
            output_item.pop("all", None)
            for node_id in nodes:
                output_item = dict(output_item)
                output_item["id"] = node_id
                parsed.append(output_item)

    return parsed


def get_node_id(graph: networkx.DiGraph, label: str) -> Optional[NodeIdType]:
    for node_id, node_attrs in graph.nodes.items():
        node_label = get_node_label(node_id, node_attrs)
        if label == node_label:
            return node_id


def extract_output_values(
    node_id: NodeIdType, task_or_outputs: Union[Task, Mapping], outputs: List[dict]
) -> Optional[dict]:
    """Output items have the following keys:
    * id: node id
    * label (optional): used when id is missing
    * name (optional): output variable name (all outputs when missing)
    * new_name (optional): optional renaming when name is defined
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
            task_output_values = task_or_outputs.output_values
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
    * id: node id
    * label (optional): used when id is missing
    * name (optional): output variable name (all outputs when missing)
    * new_name (optional): optional renaming when name is defined
    """
    task_output_values = extract_output_values(node_id, task_or_outputs, outputs)
    if task_output_values is not None:
        if merge_outputs:
            output_values.update(task_output_values)
        else:
            output_values[node_id] = task_output_values
