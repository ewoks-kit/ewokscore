from typing import Optional
from .task import Task
from .progress import BaseProgress


class TaskWithProgress(Task, register=False):
    """
    Task within a progress to display task advancement
    """

    def __init__(self, progress: Optional[BaseProgress] = None, **kw):
        super().__init__(**kw)
        self._task_progress = progress

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
            self._task_progress.progress = progress
