import sqlite3
from typing import Iterable
from .base import EwoksEventReader, EventType


class Sqlite3EwoksEventReader(EwoksEventReader):
    def __init__(self, uri: str) -> None:
        super().__init__()
        self._uri = uri
        self.__connection = None

    def close(self):
        if self.__connection is not None:
            self.__connection.close()
            self.__connection = None
        super().close()

    @property
    def _connection(self):
        if self.__connection is None:
            self.__connection = sqlite3.connect(self._uri, uri=True)
        return self.__connection

    def wait_events(self, **kwargs) -> Iterable[EventType]:
        yield from self.poll_events(**kwargs)

    def get_events(self, **filters) -> Iterable[EventType]:
        direct_filter, indirect_filter = self.split_filter(**filters)

        cursor = self._connection.cursor()
        if direct_filter:
            conditions = " AND ".join(
                [
                    f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}"
                    for k, v in direct_filter.items()
                ]
            )
            query = f"SELECT * FROM ewoks_events WHERE {conditions}"
        else:
            query = "SELECT * FROM ewoks_events"
        cursor.execute(query)
        rows = cursor.fetchall()
        self._connection.commit()

        fields = self.all_fields()
        for values in rows:
            event = dict(zip(fields, values))
            if self.match_indirect_filter(event, **indirect_filter):
                yield event
