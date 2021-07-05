"""Representation of instances of task graphs

https://networkx.org/documentation/stable/reference/readwrite/index.html
"""

from ewokscore.utils import qualname
from .tasks import SumTask, CondSumTask, ErrorSumTask


def empty_graph():
    return dict(), dict()


def acyclic_graph1():
    nodes = [
        {"id": "task1", "inputs": {"a": 1}, "class": qualname(SumTask)},
        {"id": "task2", "inputs": {"a": 2}, "class": qualname(SumTask)},
        {"id": "task3", "inputs": {"b": 3}, "class": qualname(SumTask)},
        {"id": "task4", "inputs": {"b": 4}, "class": qualname(SumTask)},
        {"id": "task5", "inputs": {"b": 5}, "class": qualname(SumTask)},
        {"id": "task6", "inputs": {"b": 6}, "class": qualname(SumTask)},
    ]

    links = [
        {"source": "task1", "target": "task3", "arguments": {"a": "result"}},
        {"source": "task2", "target": "task4", "arguments": {"a": "result"}},
        {"source": "task3", "target": "task5", "arguments": {"a": "result"}},
        {"source": "task4", "target": "task5", "arguments": {"b": "result"}},
        {"source": "task5", "target": "task6", "arguments": {"a": "result"}},
    ]

    graph = {
        "directed": True,
        "graph": {"name": qualname(acyclic_graph1)},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    expected_results = {
        "task1": {"result": 1},
        "task2": {"result": 2},
        "task3": {"result": 4},
        "task4": {"result": 6},
        "task5": {"result": 10},
        "task6": {"result": 16},
    }

    return graph, expected_results


def acyclic_graph2():
    nodes = [
        {"id": "task1", "inputs": {"a": 1}, "class": qualname(ErrorSumTask)},
        {
            "id": "task2",
            "inputs": {"b": 2, "raise_error": True},
            "class": qualname(ErrorSumTask),
        },
        {"id": "task3", "inputs": {"b": 3}, "class": qualname(ErrorSumTask)},
        {
            "id": "task4",
            "inputs": {"a": 3, "b": 4},
            "class": qualname(ErrorSumTask),
        },
        {"id": "task5", "inputs": {"b": 5}, "class": qualname(ErrorSumTask)},
        {"id": "task6", "inputs": {"b": 6}, "class": qualname(ErrorSumTask)},
    ]

    links = [
        {"source": "task1", "target": "task2", "arguments": {"a": "result"}},
        {"source": "task2", "target": "task3", "arguments": {"a": "result"}},
        {
            "source": "task2",
            "target": "task4",
            "on_error": True,
        },
        {"source": "task3", "target": "task5", "arguments": {"a": "result"}},
        {"source": "task4", "target": "task6", "arguments": {"a": "result"}},
    ]

    graph = {
        "directed": True,
        "graph": {"name": qualname(acyclic_graph2)},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }

    expected_results = {
        "task1": {"result": 1},
        "task2": None,  # error
        "task3": None,  # error branch
        "task4": {"result": 7},
        "task5": None,  # error branch
        "task6": {"result": 13},
    }

    return graph, expected_results


def cyclic_graph1():
    nodes = [
        {"id": "task1", "inputs": {"a": 1}, "class": qualname(CondSumTask)},
        {"id": "task2", "inputs": {"b": 1}, "class": qualname(CondSumTask)},
        {"id": "task3", "inputs": {"b": 3}, "class": qualname(CondSumTask)},
        {"id": "task4", "inputs": {"b": -1}, "class": qualname(CondSumTask)},
        {"id": "task5", "inputs": {"b": -1}, "class": qualname(CondSumTask)},
        {"id": "task6", "inputs": {"b": 0}, "class": qualname(CondSumTask)},
        {"id": "task7", "inputs": {"b": 1}, "class": qualname(CondSumTask)},
    ]

    links = [
        {"source": "task1", "target": "task2", "arguments": {"a": "result"}},
        {"source": "task2", "target": "task3", "arguments": {"a": "result"}},
        {"source": "task3", "target": "task4", "arguments": {"a": "result"}},
        {
            "source": "task4",
            "target": "task2",
            "arguments": {"a": "result"},
            "conditions": {"too_small": True},
        },
        {
            "source": "task4",
            "target": "task5",
            "arguments": {"a": "result"},
            "conditions": {"too_small": False},
        },
        {"source": "task5", "target": "task6", "arguments": {"a": "result"}},
        {
            "source": "task6",
            "target": "task2",
            "arguments": {"a": "result"},
            "conditions": {"too_small": True},
        },
        {
            "source": "task6",
            "target": "task7",
            "arguments": {"a": "result"},
            "conditions": {"too_small": False},
        },
    ]

    expected = {"result": 12, "too_small": False}

    graph = {
        "directed": True,
        "graph": {"name": qualname(cyclic_graph1)},
        "links": links,
        "nodes": nodes,
    }

    return graph, expected


def cyclic_graph2():
    nodes = [
        {"id": "task1", "inputs": {"a": 1}, "class": qualname(CondSumTask)},
        {"id": "task2", "inputs": {"b": 1}, "class": qualname(CondSumTask)},
        {"id": "task3", "inputs": {"b": 1}, "class": qualname(CondSumTask)},
    ]
    links = [
        {
            "source": "task1",
            "target": "task2",
            "arguments": {"a": "result"},
            "conditions": {"too_small": True},
        },
        {
            "source": "task2",
            "target": "task3",
            "arguments": {"a": "result"},
            "conditions": {"too_small": True},
        },
        {
            "source": "task3",
            "target": "task1",
            "arguments": {"a": "result"},
            "conditions": {"too_small": True},
        },
    ]

    expected = {"result": 10, "too_small": False}

    graph = {
        "directed": True,
        "graph": {"name": qualname(cyclic_graph2)},
        "links": links,
        "nodes": nodes,
    }

    return graph, expected
