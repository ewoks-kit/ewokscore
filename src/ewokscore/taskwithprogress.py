from typing import Optional

from .progress import BaseProgress
from .task import Task


class TaskWithProgress(Task, register=False):
    """
    Task within a progress to display task advancement
    """

    def __init__(self, *args, **kw):
        self._task_progress: Optional[BaseProgress] = kw.pop("progress", None)
        super().__init__(*args, **kw)

    @property
    def progress(self) -> Optional[int]:
        """Task advancement. If a task progress is not provided then return
        None"""
        if self._task_progress is not None:
            return self._task_progress.progress
        else:
            return None

    @progress.setter
    def progress(self, progress: int):
        if self._task_progress:
            current = self._task_progress.progress
            self._task_progress.progress = progress
            new = self._task_progress.progress
            if current != new:
                self._send_event(event="progress", progress=new)
