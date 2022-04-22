import time
from typing import Dict, Iterable, Tuple
from ewokscore.variable import Variable, VariableContainer
from .. import send_events
from ...utils import fromisoformat


__all__ = ["EventType", "EwoksEventReader"]

EventType = Dict[str, str]


class EwoksEventReader:
    """Base class for receiving ewoks events on the client side."""

    def __del__(self):
        self.close()

    def close(self):
        pass

    @staticmethod
    def all_fields() -> Tuple[str]:
        return send_events.FIELDS

    def wait_events(self, timeout=None, **filters) -> Iterable[EventType]:
        """Yield events matching the filter until timeout is reached."""
        raise NotImplementedError

    def poll_events(self, timeout=None, period=0.1, **filters) -> Iterable[EventType]:
        """Yield events matching the filter until timeout is reached."""
        start = time.time()
        n = 0
        while True:
            try:
                events = list(self.get_events(**filters))
            except Exception as e:
                if "no such table" not in str(e):
                    raise
            else:
                events = events[n:]
                n += len(events)
                yield from events
            if timeout is not None and (time.time() - start) > timeout:
                return
            time.sleep(period)

    def get_events(self, **filters) -> Iterable[EventType]:
        """Returns all currently available events matching the filter."""
        raise NotImplementedError

    def get_events_with_variables(self, **filters) -> Iterable[EventType]:
        """`get_events` with URI dereferencing."""
        for event in self.get_events(**filters):
            self.dereference_data_uris(event)
            yield event

    def get_full_job_events(self, **filters) -> Iterable[Tuple[EventType]]:
        """Returns events grouped by "job_id". When one event matches the filter,
        all events with the "job_id" are returned.
        """
        job_id = None
        for event in self.get_events(**filters):
            if job_id != event["job_id"]:
                job_id = event["job_id"]
                yield tuple(self.get_events(job_id=job_id))

    def get_full_job_events_with_variables(
        self, **filters
    ) -> Iterable[Tuple[EventType]]:
        """`get_full_job_events` with URI dereferencing."""
        job_id = None
        for event in self.get_events(**filters):
            if job_id != event["job_id"]:
                job_id = event["job_id"]
                yield tuple(self.get_events_with_variables(job_id=job_id))

    @staticmethod
    def dereference_data_uris(event: EventType) -> None:
        if "input_uris" in event:
            inputs = {
                uri["name"]: Variable(data_uri=uri["value"])
                if uri["value"]
                else Variable()
                for uri in event["input_uris"]
            }
            event["inputs"] = VariableContainer(inputs)
        if "task_uri" in event:
            event["outputs"] = VariableContainer(data_uri=event["task_uri"])

    @staticmethod
    def match_indirect_filter(event: EventType, starttime=None, endtime=None) -> bool:
        if not (starttime or endtime):
            return True
        time = fromisoformat(event["time"])
        if starttime is not None:
            if isinstance(starttime, str):
                starttime = fromisoformat(starttime)
            if time < starttime:
                return False
        if endtime is not None:
            if isinstance(endtime, str):
                endtime = fromisoformat(endtime)
            if time > endtime:
                return False
        return True

    @staticmethod
    def split_filter(starttime=None, endtime=None, **direct_filter):
        return direct_filter, {"starttime": starttime, "endtime": endtime}
