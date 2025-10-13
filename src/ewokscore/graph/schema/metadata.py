from typing import Callable
from typing import Optional
from typing import Tuple

import networkx
from packaging.version import parse as parse_version


class SchemaMetadata:
    """
    Metadata associated to each schema version:

        - ewokscore bounds: Versions of ewokscore that support this schema version
        - update method: A function that updates this schema version to the next one
    """

    def __init__(
        self,
        ewokscore_bounds: Tuple[str, Optional[str]],
        update_method: Optional[Callable[[networkx.DiGraph], None]],
    ) -> None:
        lower, upper = ewokscore_bounds
        if upper:
            self.ewokscore_bounds = parse_version(lower), parse_version(upper)
        else:
            self.ewokscore_bounds = parse_version(lower), None
        self.update_method = update_method
