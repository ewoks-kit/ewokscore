import sys
from enum import Enum
import logging

_logger = logging.getLogger(__name__)


class BaseProgress:
    """
    Interface to define a Task progress.
    """

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, progress):
        self._progress = progress
        self.update()

    def reset(self):
        raise NotImplementedError("Base class")

    def update(self):
        """
        Update is call when the progress evolves
        :return:
        """
        raise NotImplementedError("Base class")


class BasePercentageProgress(BaseProgress):
    """
    Define a progress in [0, 100] %
    """

    def __init__(self):
        super().__init__()
        self._progress = 0
        self._lastUpdate = None

    @BaseProgress.progress.setter
    def progress(self, progress):
        if not isinstance(progress, (int, float)):
            raise TypeError("Progress is expected to be an int or a float")
        if not (0 <= progress <= 100):
            _logger.warning("progress is expected to be in [0, 100]. Clip it")
            progress = min(max(0, progress), 100)
        BaseProgress.progress.fset(self, int(progress))

    def reset(self):
        self._lastUpdate = None
        self._progress = 0
        self.update()

    def update(self):
        if self._progress != self._lastUpdate:
            self._lastUpdate = self._progress
            self._update()

    def _update(self):
        raise NotImplementedError("Base class")


class _TextAdvancement(Enum):
    step_1 = "\\"
    step_2 = "-"
    step_3 = "/"
    step_4 = "|"

    @staticmethod
    def getNextStep(step):
        if step is _TextAdvancement.step_1:
            return _TextAdvancement.step_2
        elif step is _TextAdvancement.step_2:
            return _TextAdvancement.step_3
        elif step is _TextAdvancement.step_3:
            return _TextAdvancement.step_4
        else:
            return _TextAdvancement.step_1

    @staticmethod
    def getStep(value):
        if value % 4 == 0:
            return _TextAdvancement.step_4
        elif value % 3 == 0:
            return _TextAdvancement.step_3
        elif value % 2 == 0:
            return _TextAdvancement.step_2
        else:
            return _TextAdvancement.step_1


class TextProgress(BasePercentageProgress):
    """Print advancement in sys.stdout"""

    def __init__(self, name, char_length=20):
        super().__init__()
        self._name = name
        self._char_length = char_length

    @property
    def char_length(self):
        """how many character we want to use to represent the advancement"""
        return self._char_length

    @char_length.setter
    def char_length(self, length: int):
        if not isinstance(length, int):
            raise TypeError("length is expected to be an int")
        self._char_length = length

    @property
    def name(self) -> str:
        return self._name

    def _update(self):
        progress = self.progress
        if progress is None:
            progress = 0
        block = int(round(self.char_length * progress / 100))
        msg = "\r{0}: [{1}] {2}%".format(
            self.name,
            "#" * block + "-" * (self.char_length - block),
            round(progress, 2),
        )
        if progress >= 100:
            msg += " DONE\r\n"
        sys.stdout.write(msg)
        sys.stdout.flush()
