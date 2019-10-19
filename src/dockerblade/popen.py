# -*- coding: utf-8 -*-
__all__ = ('Popen',)

from typing import Optional, Iterator, Dict, Any
import time
import signal
import subprocess

from docker import APIClient as DockerAPIClient
from docker.models.containers import Container as DockerContainer
from loguru import logger
import attr
import docker

from .stopwatch import Stopwatch
from .exceptions import TimeoutExpired


def host_pid_to_container_pid(pid_host: int) -> Optional[int]:
    fn_proc = f'/proc/{pid_host}/status'
    try:
        with open(fn_proc, 'r') as fh:
            for line in fh:
                if line.startswith('NSpid:'):
                    return int(line.split()[2])
        return None
    except FileNotFoundError:
        return None


@attr.s(slots=True, eq=False, hash=False)
class Popen:
    """Provides access to a process that is running inside a given shell.
    Inspired by the :class:`subprocess.Popen` interface within the Python
    standard library. Unlike :class:`subprocess.Popen`, instances of this
    class should be generated by :meth:`ShellProxy.popen` rather than via
    the constructor.

    Attributes
    ----------
    stream: Iterator[str]
        An output stream for this process.
    args: str
        The argument string that was used to generate this process.
    cwd: str
        The absolute path of the directory in the container where this
        command should be executed.
    pid: int, optional
        The PID of this process, if known.
    finished: bool
        A dynamic flag (i.e., a property) that indicates whether this process
        has terminated.
    retcode: int, optional
        The return code produced by this process, if known.
    """
    args: str = attr.ib()
    cwd: str = attr.ib()
    _container: DockerContainer = attr.ib()
    _docker_api: DockerAPIClient = attr.ib(repr=False)
    _exec_id: int = attr.ib()
    _stream: Iterator[bytes] = attr.ib(repr=False)
    _pid: Optional[int] = attr.ib(init=False, default=None, repr=False)
    _pid_host: Optional[int] = attr.ib(init=False, default=None)
    _returncode: Optional[int] = attr.ib(init=False, default=None)

    def _inspect(self) -> Dict[str, Any]:
        return self._docker_api.exec_inspect(self._exec_id)

    @property
    def stream(self) -> Iterator[str]:
        for line_bytes in self._stream:
            yield line_bytes.decode('utf-8')

    @property
    def host_pid(self) -> Optional[int]:
        if not self._pid_host:
            self._pid_host = self._inspect()['Pid']
        return self._pid_host

    @property
    def pid(self) -> Optional[int]:
        host_pid = self.host_pid
        if not self._pid and host_pid:
            self._pid = host_pid_to_container_pid(host_pid)
        return self._pid

    @property
    def finished(self) -> bool:
        return self.returncode is not None

    @property
    def returncode(self) -> Optional[int]:
        if self._returncode is None:
            self._returncode = self._inspect()['ExitCode']
        return self._returncode

    def send_signal(self, sig: int) -> None:
        """Sends a given signal to the process.

        Parameters
        ----------
        sig: int
            The signal number.
        """
        pid = self.pid
        docker_container = self._container._docker
        logger.debug(f"sending signal {sig} to process {pid}")
        cmd = f'kill -{sig} -{pid}'
        if pid:
            docker_container.exec_run(cmd,
                                      stdout=False, stderr=False, user='root')

    def kill(self) -> None:
        """Kills the process via a SIGKILL signal."""
        self.send_signal(signal.SIGKILL)

    def terminate(self) -> None:
        """Terminates the process via a SIGTERM signal."""
        self.send_signal(signal.SIGTERM)

    def poll(self) -> Optional[int]:
        """Checks if the process has terminated and returns its returncode."""
        return self.returncode

    def wait(self, time_limit: Optional[float] = None) -> int:
        """Blocks until the process has terminated.

        Parameters
        ----------
        time_limit: float, optional
            An optional time limit.
        Raises
        ------
        TimeoutExpired:
            if the process does not terminate within the specified timeout.
        """
        stopwatch = Stopwatch()
        stopwatch.start()
        while not self.finished:
            if time_limit and stopwatch.duration > time_limit:
                logger.debug("timeout")
                raise TimeoutExpired(self.args, time_limit)
            time.sleep(0.05)
        assert self.returncode is not None
        return self.returncode
