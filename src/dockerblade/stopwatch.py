# -*- coding: utf-8 -*-
__all__ = ('Stopwatch',)

from timeit import default_timer as timer
import warnings

import attr


@attr.s(slots=True, repr=False)
class Stopwatch:
    """Used to record the duration of events.

    Attributes
    ----------
    paused: bool
        Indicates whether or not this stopwatch is paused.
    duration: float
        The number of seconds that the stopwatch has been running.
    """
    _offset: float = attr.ib(default=0.0)
    _paused: bool = attr.ib(default=True)
    _time_start: float = attr.ib(default=0.0)

    def __repr__(self) -> str:
        return f'Stopwatch(paused={self._paused}, duration={self.duration})'

    def stop(self) -> None:
        """Freezes the stopwatch."""
        if not self._paused:
            self._offset += timer() - self._time_start
            self._paused = True

    def start(self) -> None:
        """Resumes the stopwatch."""
        if self._paused:
            self._time_start = timer()
            self._paused = False
        else:
            warnings.warn("timer is already running")

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def duration(self) -> float:
        d = self._offset
        if not self._paused:
            d += timer() - self._time_start
        return d
