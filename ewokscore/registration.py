from typing import Optional, List
from . import utils


class Registered:
    _SUBCLASS_REGISTRY = None

    def __init_subclass__(cls, register=True, registry_name=None, **kwargs):
        super().__init_subclass__(**kwargs)

        # Ensures that not all subclasses share the same registry
        if cls._SUBCLASS_REGISTRY is None:
            cls._SUBCLASS_REGISTRY = dict()

        if not register:
            cls.__REGISTRY_NAME = None
            return

        # Register the subclass
        if registry_name:
            reg_name = registry_name
        else:
            reg_name = utils.qualname(cls)
        ecls = cls._SUBCLASS_REGISTRY.get(reg_name)
        if ecls is not None:
            raise NotImplementedError(
                f"Registry name {reg_name} is already taken by {repr(ecls)}"
            )
        cls.__REGISTRY_NAME = reg_name
        cls._SUBCLASS_REGISTRY[reg_name] = cls

    @classmethod
    def class_registry_name(cls) -> Optional[str]:
        return cls.__REGISTRY_NAME

    @classmethod
    def get_subclass_names(cls) -> List[str]:
        return list(cls._SUBCLASS_REGISTRY.keys())

    @classmethod
    def get_subclasses(cls):
        return list(cls._SUBCLASS_REGISTRY.values())

    @classmethod
    def get_subclass(cls, reg_name, _second_attempt=False):
        """Retrieving a derived class"""
        subclass = cls._SUBCLASS_REGISTRY.get(reg_name)
        if subclass is None:
            candidates = []
            for name, value in cls._SUBCLASS_REGISTRY.items():
                if name.endswith("." + reg_name):
                    candidates.append(name)
            if len(candidates) == 1:
                subclass = cls._SUBCLASS_REGISTRY.get(candidates[0])
        if subclass is None:
            if _second_attempt:
                lst = cls.get_subclass_names()
                raise RuntimeError(
                    f"Class {repr(reg_name)} is not imported. Imported classes are {repr(lst)}"
                )
            else:
                utils.import_qualname(reg_name)
                subclass = cls.get_subclass(reg_name, _second_attempt=True)
        return subclass
