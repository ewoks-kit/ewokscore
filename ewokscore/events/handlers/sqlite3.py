from .base import EwoksEventHandlerMixIn
from ...logging_utils.handlers import Sqlite3Handler


class Sqlite3EwoksEventHandler(EwoksEventHandlerMixIn, Sqlite3Handler):
    def __init__(self, uri: str):
        super().__init__(uri=uri, table="ewoks_events", fields=self.all_fields())
