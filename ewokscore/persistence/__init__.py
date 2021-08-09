from .proxy import DataProxy
from .json import JsonProxy  # noqa F401
from .nexus import NexusProxy  # noqa F401


def instantiate_data_proxy(scheme, *args, **kw):
    return DataProxy.instantiate(scheme, *args, **kw)
