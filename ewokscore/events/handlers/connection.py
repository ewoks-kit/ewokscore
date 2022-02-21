import time
import logging.handlers


class ConnectionHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._connection = None
        self.closeOnError = False
        self._retry_time = None
        #
        # Exponential backoff parameters.
        #
        self._retry_start = 1.0
        self._retry_max = 30.0
        self._retry_factor = 2.0

    def _connect(self, timeout=1) -> None:
        raise NotImplementedError

    def _disconnect(self) -> None:
        raise NotImplementedError

    def _send_serialized_record(self, record):
        raise NotImplementedError

    def _serialize_record(self, record):
        raise NotImplementedError

    def _connected(self) -> bool:
        return self._connection is not None

    def ensure_connection(self) -> bool:
        if self._connected():
            return True
        now = time.time()
        if self._retry_time is not None and now < self._retry_time:
            return
        self._connect()
        if self._connected():
            # Connection succeeded: no delay for next connection attempt
            self._retry_time = None
            return True
        # Connection failed: no next connection attempt before _retry_time
        if self._retry_time is None:
            self._retry_period = self._retry_start
        else:
            self._retry_period = self._retry_period * self._retry_factor
            if self._retry_period > self._retry_max:
                self._retry_period = self._retry_max
        self._retry_time = now + self._retry_period
        return False

    def handleError(self, record):
        if self.closeOnError and self._connected():
            self._disconnect()
        else:
            super().handleError(record)

    def emit(self, record):
        try:
            if self.ensure_connection():
                s = self._serialize_record(record)
                self._send_serialized_record(s)
        except Exception:
            self.handleError(record)

    def close(self):
        self.acquire()
        try:
            if self._connected():
                self._disconnect()
            super().close()
        finally:
            self.release()
