import networkx
from pprint import pprint
import matplotlib.pyplot as plt
from ewokscore import load_graph
from ewokscore.variable import Variable


def assert_taskgraph_result(taskgraph, expected, varinfo):
    tasks = dict()
    taskgraph = load_graph(taskgraph)
    assert not taskgraph.is_cyclic, "Can only check DAG results"

    for node in taskgraph.graph.nodes:
        task = taskgraph.instantiate_task_static(node, tasks=tasks, varinfo=varinfo)
        value = expected.get(node)
        if value is None:
            assert not task.done, node
        else:
            assert task.done, node
            try:
                assert task.output_values == value, node
            except AssertionError:
                raise
            except Exception as e:
                raise RuntimeError(f"{node} does not have a result") from e


def assert_taskgraph_result_output(result, expected, varinfo):
    for k, v in expected.items():
        uhash = result[k]
        var = Variable(uhash=uhash, varinfo=varinfo)
        assert var.value == v


def show_graph(graph, stdout=True, plot=True, show=True):
    taskgraph = load_graph(graph)
    if stdout:
        pprint(taskgraph.dump())
    if plot:
        networkx.draw(taskgraph.graph, with_labels=True, font_size=10)
        if show:
            plt.show()
