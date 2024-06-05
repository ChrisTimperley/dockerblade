from __future__ import annotations

__all__ = ("Stopwatch",)

import typing as t
import warnings
from timeit import default_timer as timer

import attr

if t.TYPE_CHECKING:
    from types import TracebackType


@attr.s(slots=True, repr=False, str=False, eq=False, hash=False)
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

    def __enter__(self) -> t.Self:
        self.start()
        return self

    def __exit__(
        self,
        ex_type: type[BaseException] | None,
        ex_val: BaseException | None,
        ex_tb: TracebackType | None,
    ) -> None:
        self.stop()

    def __repr__(self) -> str:
        return f"Stopwatch(paused={self._paused}, duration={self.duration})"

    def __str__(self) -> str:
        status = "PAUSED" if self._paused else "RUNNING"
        return f"[{status}] {self.duration:.3f} s"

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
            warnings.warn(
                "timer is already running",
                stacklevel=2,
            )

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def duration(self) -> float:
        d = self._offset
        if not self._paused:
            d += timer() - self._time_start
        return d
