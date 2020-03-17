# -*- coding: utf-8 -*-
import typing as _t
import attr as _attr
import subprocess as _subprocess


class DockerBladeException(Exception):
    """Used by all exceptions that are thrown by DockerBlade."""


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class UnexpectedError(DockerBladeException):
    """An unexpected error occurred during an operation."""
    description: str
    error: _t.Optional['CalledProcessError'] = _attr.ib(default=None)

    def __str__(self) -> str:
        msg = f"An unexpected error occurred: {self.description}"
        if self.error:
            msg += f' ({self.error})'
        return msg


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class EnvNotFoundError(DockerBladeException):
    """No environment variable was found with the given name."""
    name: str

    def __str__(self) -> str:
        return f"No environment variable found with name: {self.name}"


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class CopyFailed(DockerBladeException):
    """A copy operation failed unexpectedly."""
    reason: str

    def __str__(self) -> str:
        return 'Copy operation failed: {self.reason}'


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class IsADirectoryError(DockerBladeException):
    """The given path is a directory but a file was expected."""
    path: str

    def __str__(self) -> str:
        return f'Directory exists at path where file is expected: {self.path}'


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class DirectoryNotEmpty(DockerBladeException):
    """A given directory is not empty."""
    path: str

    def __str__(self) -> str:
        return f'Directory is not empty: {self.path}'


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class IsNotADirectoryError(DockerBladeException):
    """The given path is not a directory."""
    path: str

    def __str__(self) -> str:
        return f'Directory was expected at path: {self.path}'


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class HostFileNotFound(DockerBladeException):
    """No file was found at a given path on the host machine."""
    path: str

    def __str__(self) -> str:
        return f'File not found [{self.path}] on host machine'


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class ContainerFileNotFound(DockerBladeException):
    """No file was found at a given path in a container."""
    container_id: str
    path: str

    def __str__(self) -> str:
        return (f'File not found [{self.path}] '
                f'in container [{self.container_id}]')


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class ContainerFileAlreadyExists(DockerBladeException):
    """A file already exists at a given path inside a container."""
    container_id: str
    path: str

    def __str__(self) -> str:
        return (f'File already exists [{self.path}] '
                f'in container [{self.container_id}]')


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class CalledProcessError(DockerBladeException, _subprocess.CalledProcessError):
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
    output: _t.Optional[_t.Union[str, bytes]]


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True)
class TimeoutExpired(DockerBladeException, _subprocess.TimeoutExpired):
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
