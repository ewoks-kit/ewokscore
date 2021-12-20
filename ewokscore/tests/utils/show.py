import networkx
from pprint import pprint
from ewokscore import load_graph


def show_graph(graph, stdout=True, plot=True, show=True):
    taskgraph = load_graph(graph)
    if stdout:
        pprint(taskgraph.dump())
    if plot:
        networkx.draw(taskgraph.graph, with_labels=True, font_size=10)
        if show:
            import matplotlib.pyplot as plt

            plt.show()
