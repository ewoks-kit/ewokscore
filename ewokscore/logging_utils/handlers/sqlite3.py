import time
import json
import sqlite3
from typing import Iterable, List, Optional
from .connection import ConnectionHandler


class Sqlite3Handler(ConnectionHandler):
    def __init__(self, uri: str, table: str, fields: Iterable[str]):
        self._uri = uri
        self._fields = list(fields)
        fields = ",".join([f"{field} TEXT" for field in self._fields])
        ensure_table = f"CREATE TABLE IF NOT EXISTS {table}({fields})"
        self._ensure_table_query = ensure_table
        values = ("?," * len(self._fields))[:-1]
        self._insert_row_query = f"INSERT INTO {table} VALUES({values})"
        super().__init__()

    def _connect(self, timeout=1) -> None:
        try:
            conn = sqlite3.connect(
                self._uri, timeout=timeout, uri=True, check_same_thread=False
            )
            self._sql_query(self._ensure_table_query, conn=conn)
        except (OSError, TimeoutError):
            self._connection = None
        else:
            self._connection = conn

    def _disconnect(self) -> None:
        self._connection.close()

    def _send_serialized_record(self, values: Optional[List[Optional[str]]]):
        if values:
            self._sql_query(self._insert_row_query, values)

    def _serialize_record(self, record) -> Optional[List[Optional[str]]]:
        return [self.get_value(record, field) for field in self._fields]

    @staticmethod
    def get_value(record, field) -> Optional[str]:
        value = getattr(record, field, None)
        if value is None:
            return value
        elif isinstance(value, str):
            return value
        else:
            return json.dumps(value)

    def _sql_query(
        self, sql: str, parameters: Iterable = tuple(), conn=None, timeout=1
    ) -> None:
        if conn is None:
            conn = self._connection
        exception = None
        t0 = time.time()
        while True:
            try:
                conn.execute(sql, parameters)
                break
            except sqlite3.OperationalError as e:
                exception = e
            t1 = time.time()
            if timeout is not None and (t1 - t0) > timeout:
                raise TimeoutError("cannot execute SQL query") from exception
        while True:
            try:
                conn.commit()
                break
            except sqlite3.OperationalError as e:
                exception = e
            t1 = time.time()
            if timeout is not None and (t1 - t0) > timeout:
                raise TimeoutError("cannot commit SQL query") from exception
