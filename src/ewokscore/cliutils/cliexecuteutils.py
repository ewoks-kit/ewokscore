from . import utils


def add_execute_parameters(parser):
    parser.add_argument(
        "workflow",
        type=str,
        help="Workflow to execute(e.g. JSON filename)",
    )
    parser.add_argument(
        "--workflow-dir",
        type=str,
        default="",
        dest="workflow_dir",
        help="Directory of sub-workflows (current working directory by default)",
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
        "-j",
        "--jobid",
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
        help="The 'workflow' argument refers to the name of a test graph",
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["none", "end", "all"],
        default="none",
        help="Log outputs (per task or merged values dictionary)",
    )
    parser.add_argument(
        "--merge-outputs",
        action="store_true",
        dest="merge_outputs",
        help="Merge node outputs",
    )


def apply_execute_parameters(args):
    args.graph = utils.parse_workflow(args)

    execute_options = dict(utils.parse_option(item) for item in args.options)

    execute_options["inputs"] = [
        utils.parse_parameter(input_item) for input_item in args.parameters
    ]

    if args.output == "all":
        execute_options["outputs"] = [{"all": True}]
    elif args.output == "end":
        execute_options["outputs"] = [{"all": False}]
    else:
        execute_options["outputs"] = []
    execute_options["merge_outputs"] = args.merge_outputs

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
                    "class": "ewokscore.events.handlers.Sqlite3EwoksEventHandler",
                    "arguments": [{"name": "uri", "value": args.sqlite3_uri}],
                }
            ]

    args.execute_options = execute_options
