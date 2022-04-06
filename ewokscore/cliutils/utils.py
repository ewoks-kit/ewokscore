import json
from typing import Tuple, Any


def parse_value(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return value


def parse_parameter(input_item: str):
    node_and_name, _, value = input_item.partition("=")
    label, _, name = node_and_name.partition(":")
    value = parse_value(value)
    if name:
        return {"label": label, "name": name, "value": value}
    else:
        return {"name": label, "value": value}  # all input nodes


def parse_option(option: str) -> Tuple[str, Any]:
    option, _, value = option.partition("=")
    return option, parse_value(value)


def parse_workflow(args):
    if args.test:
        from ewokscore.tests.examples.graphs import graph_names, get_graph

        graphs = list(graph_names())
        if args.workflow not in graphs:
            raise RuntimeError(f"Test graph '{args.workflow}' does not exist: {graphs}")

        graph, _ = get_graph(args.workflow)
    else:
        graph = args.workflow
    return graph
