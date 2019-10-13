# -*- coding: utf-8 -*-
import typing as t_
import attr as _attr


class DockerBladeException(Exception):
    """Used by all exceptions that are thrown by DockerBlade."""


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class EnvNotFoundError(DockerBladeException):
    """No environment variable was found with the given name."""
    name: str

    def __str__(self) -> str:
        return f"No environment variable found with name: {self.name}"


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class CalledProcessError(DockerBladeException):
    """Thrown when a process produces a non-zero return code.

    Attributes
    ----------
    cmd: str
        The command that was used to launch the process.
    returncode: int
        The returncode that was produced by the process.
    duration: float
        The number of seconds that elapsed before the process terminated.
    output: T, optional
        The output, if any, that was produced by the process.
    """
    cmd: str
    returncode: int
    duration: float
    output: t_.Optional[t_.Union[str, bytes]]


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class TimeoutExpired(DockerBladeException):
    """Thrown when a timeout expires while waiting for a process.

    Attributes
    ----------
    cmd: str
        The command that was used to launch the process.
    timeout: float
        The timeout in seconds.
    """
    cmd: str
    timeout: float
