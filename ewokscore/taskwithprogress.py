from typing import Union
from .task import Task
from .progress import BaseProgress


class TaskWithProgress(Task):
    """
    Task within a progress to display task advancement
    """

    def __init__(
        self, inputs=None, varinfo=None, progress: Union[None, BaseProgress] = None
    ):
        super().__init__(inputs=inputs, varinfo=varinfo)
        self._task_progress = progress

    @property
    def progress(self) -> Union[None, int]:
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
