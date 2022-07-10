from typing import Any, Dict, Optional, Union
from ewokscore.graph import load_graph
from ewokscore.graph.taskgraph import TaskGraph
from ewokscore.node import NodeIdType
from ewokscore.task import Task
from ewokscore import missing_data
from ewokscore.variable import value_from_transfer
from ewokscore.graph.analysis import end_nodes
from ewokscore.graph.execute.sequential import instantiate_task_static


def assert_execute_graph_default_result(
    taskgraph: Union[TaskGraph, dict],
    result: Dict[str, Any],
    expected: Dict[str, Any],
    varinfo: Optional[dict] = None,
):
    """The default result is the merged output of all end nodes."""
    if varinfo:
        scheme = varinfo.get("scheme")
    else:
        scheme = None
    taskgraph = load_graph(taskgraph)
    if taskgraph.is_cyclic:
        expected = filter_expected_results(
            taskgraph, expected, end_only=True, merge=True
        )
        assert_execute_graph_values(result, expected, varinfo)
    elif scheme:
        _assert_execute_graph_tasks(taskgraph, expected, varinfo=varinfo)
        expected = filter_expected_results(
            taskgraph, expected, end_only=True, merge=True
        )
        assert_execute_graph_values(result, expected, varinfo)
    else:
        expected = filter_expected_results(
            taskgraph, expected, end_only=True, merge=True
        )
        assert_execute_graph_values(result, expected, varinfo)


def assert_execute_graph_tasks(
    taskgraph: Union[TaskGraph, dict],
    result: Dict[str, Any],
    expected: Dict[str, Any],
    varinfo: Optional[dict] = None,
):
    if varinfo:
        scheme = varinfo.get("scheme")
    else:
        scheme = None
    _assert_execute_graph_tasks(
        taskgraph, expected, varinfo=varinfo, execute_graph_result=result
    )
    if scheme and result:
        _assert_execute_graph_tasks(taskgraph, expected, varinfo=varinfo)


def _assert_execute_graph_tasks(
    taskgraph: Union[TaskGraph, dict],
    expected: Dict[NodeIdType, Any],
    varinfo: Optional[dict] = None,
    execute_graph_result: Optional[Dict[NodeIdType, Task]] = None,
):
    """Check the output of `execute_graph` for each node. When a task is not in `execute_graph_result`,
    it will be instantiated.

    An expected value can be:
        * `None`: task is not executed and therefore does not appear in the results
        * `MISSING_DATA`: task has no output and is therefore cannot be persisted
        * else: task is executed and has output
    """
    taskgraph = load_graph(taskgraph)
    assert not taskgraph.is_cyclic, "Can only check DAG results"

    if execute_graph_result is None:
        execute_graph_result = dict()

    for node in taskgraph.graph.nodes:
        task = execute_graph_result.get(node, None)
        loaded = False
        if task is None:
            assert varinfo, "Need 'varinfo' to load task output"
            task = instantiate_task_static(
                taskgraph.graph, node, tasks=execute_graph_result, varinfo=varinfo
            )
            loaded = True
        assert_task_result(task, node, expected, loaded)


def assert_execute_graph_values(
    execute_graph_result: Dict[str, Any],
    expected: Dict[str, Any],
    varinfo: Optional[dict] = None,
):
    """Check the output of `execute_graph` for the selected outputs of the selected nodes."""
    for output_name, expected_value in expected.items():
        value = execute_graph_result[output_name]
        assert_result(value, expected_value, varinfo=varinfo)


def assert_task_result(task: Task, node_id: NodeIdType, expected: dict, loaded: bool):
    expected_value = expected.get(node_id)
    if missing_data.is_missing_data(expected_value):
        if loaded:
            expected_value = None
        else:
            expected_value = dict()

    if expected_value is None:
        assert not task.done, node_id
    else:
        assert task.done, node_id
        try:
            assert task.output_values == expected_value, node_id
        except AssertionError:
            raise
        except Exception as e:
            raise RuntimeError(f"{node_id} does not have a result") from e


def assert_result(value, expected_value, varinfo: Optional[dict] = None):
    value = value_from_transfer(value, varinfo=varinfo)
    assert value == expected_value


def filter_expected_results(
    taskgraph: Union[TaskGraph, dict],
    results: Dict[NodeIdType, Any],
    end_only: bool = False,
    merge: bool = False,
) -> dict:
    taskgraph = load_graph(taskgraph)
    if end_only:
        nodes = end_nodes(taskgraph.graph)
        results = {k: v for k, v in results.items() if k in nodes}
    else:
        nodes = taskgraph.nodes()
    if merge:
        ret = dict()
        for node_id in nodes:
            adict = results.get(node_id)
            if adict:
                ret.update(adict)
        results = ret
    return results
