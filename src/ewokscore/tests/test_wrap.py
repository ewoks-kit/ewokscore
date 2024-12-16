import pytest

from ewokscore.wrap import task_asfunction


def test_no_output():
    wrapper = task_asfunction(
        "ewokscore.tests.examples.tasks.nooutputtask.NoOutputTask"
    )
    result = wrapper()
    assert result is None


def test_single_output():
    wrapper = task_asfunction("ewokscore.tests.examples.tasks.sumtask.SumTask")
    result = wrapper(a=1, b=1)
    assert result == 2


def test_multiple_outputs():
    wrapper = task_asfunction("ewokscore.tests.examples.tasks.condsumtask.CondSumTask")
    result = wrapper(a=1, b=1)
    assert result.result == 2
    assert result.too_small is True
    assert result._fields == ("result", "too_small")


def test_error():
    wrapper = task_asfunction(
        "ewokscore.tests.examples.tasks.errorsumtask.ErrorSumTask"
    )
    with pytest.raises(RuntimeError):
        wrapper(a=1, b=1, raise_error=True)
