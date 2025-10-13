from ewoksutils.logging_utils.sqlite3 import Sqlite3Handler

from .base import EwoksEventHandlerMixIn


class Sqlite3EwoksEventHandler(EwoksEventHandlerMixIn, Sqlite3Handler):
    def __init__(self, uri: str):
        super().__init__(uri=uri, table="ewoks_events", field_types=self.FIELD_TYPES)
