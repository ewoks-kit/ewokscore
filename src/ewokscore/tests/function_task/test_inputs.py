import pytest
from ewoksutils.import_utils import qualname

from ...methodtask import get_method_task
from .shared_methods import plain_model_method


def test_task_inputs_from_signature():
    task_class = get_method_task(qualname(plain_model_method))

    assert set(task_class.required_input_names()) == {"a"}
    assert set(task_class.optional_input_names()) == {"b"}
    assert set(task_class.output_names()) == {"total"}


def signature_named(a: int, b: int = 1) -> int:
    return a + b


def signature_var_args(a, *args, b=None, c=3, **kw):
    return a


def signature_keyword_only(a, *args, b):
    return a


def signature_var_kwargs(a, b=1, **kw):
    return a


def signature_positional_only(a, b, /, c, d=1):
    return a


def signature_positional_only_default(a, b=1, /, c=2):
    return a


def signature_no_arguments():
    return None


@pytest.mark.parametrize(
    "method,required,optional,n_positional,has_model",
    [
        (signature_named, {"a"}, {"b"}, 0, True),
        (signature_var_args, {"a"}, {"b", "c"}, 0, False),
        (signature_keyword_only, {"a", "b"}, set(), 0, False),
        (signature_var_kwargs, {"a"}, {"b"}, 0, False),
        (signature_positional_only, {"c"}, {"d"}, 2, False),
        (signature_positional_only_default, set(), {"c"}, 1, False),
        (signature_no_arguments, set(), set(), 0, True),
    ],
    ids=lambda value: getattr(value, "__name__", None),
)
def test_task_inputs_of_signature(method, required, optional, n_positional, has_model):
    task_class = get_method_task(qualname(method))

    assert set(task_class.required_input_names()) == required
    assert set(task_class.optional_input_names()) == optional
    assert task_class.n_required_positional_inputs() == n_positional
    assert (task_class.input_model() is not None) == has_model


def positional_only_method(a, b, /, c, d=1):
    return a + b + c + d


def test_positional_only_inputs(varinfo):
    task = get_method_task(qualname(positional_only_method))(
        inputs={0: 1, 1: 2, "c": 3}, varinfo=varinfo
    )
    task.execute()
    assert task.get_output_values() == {"return_value": 7}


def test_missing_positional_only_input(varinfo):
    task_class = get_method_task(qualname(positional_only_method))
    with pytest.raises(Exception, match="positional argument"):
        task_class(inputs={0: 1, "c": 3}, varinfo=varinfo)


def variadic_method(*args):
    return sum(args)


def test_variadic_inputs(varinfo):
    task = get_method_task(qualname(variadic_method))(
        inputs={0: 3, 1: 5}, varinfo=varinfo
    )
    task.execute()
    assert task.get_output_values() == {"return_value": 8}


def var_kwargs_method(a, b=1, **kw):
    return a + b + sum(kw.values())


def test_var_kwargs_inputs(varinfo):
    task = get_method_task(qualname(var_kwargs_method))(
        inputs={"a": 2, "b": 3, "extra": 4}, varinfo=varinfo
    )
    task.execute()
    assert task.get_output_values() == {"return_value": 9}


def test_missing_required_input(varinfo):
    task_class = get_method_task(qualname(var_kwargs_method))
    with pytest.raises(Exception, match=r"Missing inputs.*'a'"):
        task_class(inputs={"b": 3}, varinfo=varinfo)
