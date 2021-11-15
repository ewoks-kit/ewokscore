from ewokscore.utils import qualname
from ewokscore.task import Task


def mymethod1(a=0, b=0):
    return a + b


def test_method_task1(varinfo):
    task = Task.instantiate(
        "MethodExecutorTask",
        inputs={"_method": qualname(mymethod1), "a": 3, "b": 5},
        varinfo=varinfo,
    )
    task.execute()
    assert task.done
    assert task.output_values == {"return_value": 8}


def mymethod2(*args):
    return sum(args)


def test_method_task2(varinfo):
    task = Task.instantiate(
        "MethodExecutorTask",
        inputs={"_method": qualname(mymethod2), 0: 3, 1: 5},
        varinfo=varinfo,
    )
    task.execute()
    assert task.done
    assert task.output_values == {"return_value": 8}


def mymethod3(a, *args, b=None, c=3, **kw):
    print("a:", a)
    print("b:", b)
    print("c:", c)
    print("args:", args)
    print("kwargs:", kw)
    return a + sum(args) + b + c + sum(kw.values())


def test_method_task3(varinfo):
    task = Task.instantiate(
        "MethodExecutorTask",
        inputs={"_method": qualname(mymethod3), 0: 2, 1: 4, "b": 7, "d": 10},
        varinfo=varinfo,
    )
    task.execute()
    assert task.done
    assert task.output_values == {"return_value": 26}


def myppfmethod(a=0, b=0, **kw):
    return {"a": a + b}


def test_ppfmethod_task(varinfo):
    task = Task.instantiate(
        "PpfMethodExecutorTask",
        inputs={"_method": qualname(myppfmethod), "a": 3, "b": 5},
        varinfo=varinfo,
    )
    task.execute()
    assert task.done
    assert task.output_values == {"_ppfdict": {"a": 8, "b": 5}}
