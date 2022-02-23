import json
from typing import Any, Tuple


def add_execute_parameters(parser):
    parser.add_argument(
        "workflow",
        type=str,
        help="URI to a workflow (e.g. JSON filename)",
    )
    parser.add_argument(
        "--workflow-dir",
        type=str,
        default="",
        dest="workflow_dir",
        help="Directory of sub-workflows",
    )
    parser.add_argument(
        "--data-root-uri",
        type=str,
        default="",
        dest="data_root_uri",
        help="Root for saving task results",
    )
    parser.add_argument(
        "--data-scheme",
        type=str,
        choices=["nexus", "json"],
        default="nexus",
        dest="data_scheme",
        help="Default task result format",
    )
    parser.add_argument(
        "-p",
        "--parameter",
        dest="parameters",
        action="append",
        default=[],
        metavar="[NODE:]NAME=VALUE",
        help="Input variable for a particular node (or all start nodes when missing)",
    )
    parser.add_argument(
        "-o",
        "--option",
        dest="options",
        action="append",
        default=[],
        metavar="OPTION=VALUE",
        help="Execution options",
    )
    parser.add_argument(
        "-j" "--jobid",
        dest="job_id",
        type=str,
        default=None,
        help="Job id for ewoks events",
    )
    parser.add_argument(
        "--disable_events",
        dest="disable_events",
        action="store_true",
        help="Disable ewoks events",
    )
    parser.add_argument(
        "--sqlite3",
        dest="sqlite3_uri",
        type=str,
        default=None,
        help="Store ewoks events in an Sqlite3 database",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="The workflow arguments is the name of a test graph",
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["end", "all", "end_values", "all_values"],
        default="end",
        help="Log outputs (per task or merged values dictionary)",
    )


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


def apply_execute_parameters(args):
    args.graph = parse_workflow(args)

    execute_options = dict(parse_option(item) for item in args.options)

    execute_options["inputs"] = [
        parse_parameter(input_item) for input_item in args.parameters
    ]

    execute_options["results_of_all_nodes"] = args.output == "all"
    if args.output == "all_values":
        execute_options["outputs"] = [{"all": True}]
    elif args.output == "end_values":
        execute_options["outputs"] = [{"all": False}]

    execute_options["varinfo"] = {
        "root_uri": args.data_root_uri,
        "scheme": args.data_scheme,
    }
    execute_options["load_options"] = {"root_dir": args.workflow_dir}

    if not args.disable_events:
        execinfo = dict()
        execute_options["execinfo"] = execinfo
        if args.job_id:
            execinfo["job_id"] = args.job_id
        if args.sqlite3_uri:
            # TODO: asynchronous handling may loose events
            execinfo["asynchronous"] = False
            execinfo["handlers"] = [
                {
                    "class": "ewokscore.events.handlers.EwoksSqlite3EventHandler",
                    "arguments": [{"name": "uri", "value": args.sqlite3_uri}],
                }
            ]

    args.execute_options = execute_options
