from ewoksutils.logging_utils.sqlite3 import Sqlite3Handler

from .base import EwoksEventHandlerMixIn


class Sqlite3EwoksEventHandler(EwoksEventHandlerMixIn, Sqlite3Handler):
    def __init__(
        self, uri: str, timeout: float = 10, disconnect_on_error: bool = False
    ):
        """
        :param uri: for example "file:/path/to/ewoks_events.db" or
                    "file:///path/to/ewoks_events.db".
        :param timeout: native sqlite3 busy timeout: the maximum time to wait
                        for database locks to be released by other connections.
                        An event is dropped when the timeout is reached.
        :param disconnect_on_error: disconnect when emitting an event failed.
        """
        super().__init__(
            uri=uri,
            table="ewoks_events",
            field_types=self.FIELD_TYPES,
            timeout=timeout,
            disconnect_on_error=disconnect_on_error,
        )
