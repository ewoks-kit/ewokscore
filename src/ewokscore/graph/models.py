from typing import Mapping, Union
from pathlib import Path
from networkx import Graph

GraphSource = Union[str, Path, Mapping, Graph]
