from functools import lru_cache
from typing import Dict
from typing import Type

from .._conda import CondaManager
from .._pip_venv import PipVenvManager
from .._pixi import PixiManager
from .._poetry import PoetryManager
from .._uv import UvManager
from .base_manager import BaseManager


@lru_cache(1)
def get_supported_managers() -> Dict[str, Type[BaseManager]]:
    managers = [
        PipVenvManager,
        UvManager,
        PoetryManager,
        CondaManager,
        PixiManager,
    ]
    return {manager_cls.NAME: manager_cls for manager_cls in managers}
