from pathlib import Path
from typing import Mapping
from typing import Union

from networkx import Graph

GraphSource = Union[str, Path, Mapping, Graph]
