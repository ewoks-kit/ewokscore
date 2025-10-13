from .json import JsonProxy  # noqa F401
from .nexus import NexusProxy  # noqa F401
from .proxy import DataProxy

instantiate_data_proxy = DataProxy.instantiate
