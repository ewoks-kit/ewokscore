from typing import Any
from typing import Dict

import numpy

from .types import CustomType


def generate_example_data() -> Dict[str, Any]:
    value = {
        "string": "string",
        "bytes": b"bytes",
        "int": 42,
        "float": 20.3,
        "np_scalar1": numpy.uint16(10),
        "np_scalar2": numpy.float64(-10),
        "empty_list": [],
        "empty_tuple": (),
        "empty_set": set(),
        "empty_dict": {},
        "list": [-1, -2, -3],
        "tuple": (1, 2, 3),
        "nested_tuple": ("a", ("b", "c")),
        "set": {100, 200, 300},
        "np_array": numpy.array([10, 20, 30]),
        "custom_type": CustomType(42),
    }
    try:
        value["np_scalar3"] = numpy.float128(1e10)
    except AttributeError:
        pass
    return {
        **value,
        "nested_list": [value],
        "nested_tuple": (value,),
        "nested_set": {(1, 2), (3, 4)},
        "nested_dict": {"value": value},
    }
