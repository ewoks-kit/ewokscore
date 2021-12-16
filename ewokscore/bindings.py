from typing import Optional, Union, Dict, List
from .graph import load_graph
from .graph import NodeIdentifier
from .node import NodeIdType


def execute_graph(
    graph,
    inputs: Union[Dict[Union[NodeIdType, str], List[dict]], List[dict], None] = None,
    inputs_node_identifier: Union[NodeIdentifier, str, None] = None,
    load_options: Optional[dict] = None,
    **execute_options
):
    if load_options is None:
        load_options = dict()
    graph = load_graph(source=graph, **load_options)
    if inputs:
        graph.update_default_inputs(inputs, node_identifier=inputs_node_identifier)
    return graph.execute(**execute_options)
