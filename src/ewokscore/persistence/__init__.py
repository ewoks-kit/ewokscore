from .proxy import DataProxy
from .json import JsonProxy  # noqa F401
from .nexus import NexusProxy  # noqa F401

instantiate_data_proxy = DataProxy.instantiate
