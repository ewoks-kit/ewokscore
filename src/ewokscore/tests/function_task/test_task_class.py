from ewoksutils.import_utils import qualname

from ...methodtask import get_method_task
from .shared_methods import RangeInfo
from .shared_methods import range_info


def test_task_class_of_a_function():
    task_class = get_method_task(qualname(range_info))

    assert task_class is get_method_task(qualname(range_info))
    assert task_class.__name__ == "RangeInfoTask"
    assert task_class.__doc__ == "Information on the range between two numbers."


def test_function_is_callable():
    assert range_info(15, 10) == RangeInfo(extent=5, minimum=10, maximum=15)
