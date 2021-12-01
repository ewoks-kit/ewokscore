from typing import Any, Dict, Optional
import networkx
from pprint import pprint
import matplotlib.pyplot as plt
from ewokscore import load_graph
from ewokscore.graph import TaskGraph
from ewokscore.node import NodeIdType
from ewokscore.task import Task
from ewokscore.variable import value_from_transfer


def assert_taskgraph_result(
    taskgraph: TaskGraph,
    expected: Dict[NodeIdType, Any],
    varinfo: Optional[dict] = None,
    tasks: Optional[Dict[NodeIdType, Task]] = None,
):
    taskgraph = load_graph(taskgraph)
    assert not taskgraph.is_cyclic, "Can only check DAG results"

    if tasks is None:
        tasks = dict()

    for node in taskgraph.graph.nodes:
        task = tasks.get(node, None)
        if task is None:
            assert varinfo, "Need 'varinfo' to load task output"
            task = taskgraph.instantiate_task_static(node, tasks=tasks, varinfo=varinfo)
        assert_task_result(task, node, expected)


def assert_task_result(task: Task, node_id: NodeIdType, expected: dict):
    expected_value = expected.get(node_id)
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


def assert_workflow_result(
    results: Dict[NodeIdType, Any],
    expected: Dict[NodeIdType, Any],
    varinfo: Optional[dict] = None,
):
    for node_id, expected_result in expected.items():
        if expected_result is None:
            assert node_id not in results
            continue
        result = results[node_id]
        if isinstance(result, Task):
            assert result.done, node_id
            result = result.output_values
        for output_name, expected_value in expected_result.items():
            value = result[output_name]
            assert_result(value, expected_value, varinfo=varinfo)


def assert_workflow_merged_result(
    result: dict, expected: Dict[NodeIdType, Any], varinfo: Optional[dict] = None
):
    for output_name, expected_value in expected.items():
        value = result[output_name]
        assert_result(value, expected_value, varinfo=varinfo)


def assert_result(value, expected_value, varinfo: Optional[dict] = None):
    value = value_from_transfer(value, varinfo=varinfo)
    assert value == expected_value


def show_graph(graph, stdout=True, plot=True, show=True):
    taskgraph = load_graph(graph)
    if stdout:
        pprint(taskgraph.dump())
    if plot:
        networkx.draw(taskgraph.graph, with_labels=True, font_size=10)
        if show:
            plt.show()
