import networkx
from pprint import pprint
import matplotlib.pyplot as plt
from ewokscore import load_graph
from ewokscore.variable import value_from_transfer


def assert_taskgraph_result(taskgraph, expected, varinfo=None, tasks=None):
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


def assert_task_result(task, node, expected):
    expected_value = expected.get(node)
    if expected_value is None:
        assert not task.done, node
    else:
        assert task.done, node
        try:
            assert task.output_values == expected_value, node
        except AssertionError:
            raise
        except Exception as e:
            raise RuntimeError(f"{node} does not have a result") from e


def assert_workflow_result(results, expected, varinfo=None):
    for node_name, expected_result in expected.items():
        if expected_result is None:
            assert node_name not in results
            continue
        result = results[node_name]
        for output_name, expected_value in expected_result.items():
            value = result[output_name]
            assert_result(value, expected_value, varinfo=varinfo)


def assert_workflow_merged_result(result, expected, varinfo=None):
    for output_name, expected_value in expected.items():
        value = result[output_name]
        assert_result(value, expected_value, varinfo=varinfo)


def assert_result(value, expected_value, varinfo=None):
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
