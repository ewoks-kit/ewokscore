import argparse
from ewokscore import cliutils


def test_cli_execute_workflow():
    parser = argparse.ArgumentParser()
    cliutils.add_execute_parameters(parser)
    argv = ["acyclic1", "--test", "-p", "a=1", "-p", "task1:b=test"]
    args, _ = parser.parse_known_args(argv)
    cliutils.apply_execute_parameters(args)

    assert args.graph["graph"]["id"] == "acyclic1"

    execute_options = {
        "inputs": [
            {"name": "a", "value": 1},
            {"label": "task1", "name": "b", "value": "test"},
        ],
        "results_of_all_nodes": False,
        "varinfo": {"root_uri": "", "scheme": "nexus"},
        "load_options": {"root_dir": ""},
        "execinfo": {},
    }
    assert args.execute_options == execute_options
