from typing import Any
from typing import Optional
from typing import Type


def convert_if_equal(value: Any, new_type: Type) -> Optional[Any]:
    try:
        new_value = new_type(value)
        if value == new_value:
            return new_value
    except Exception:
        pass
