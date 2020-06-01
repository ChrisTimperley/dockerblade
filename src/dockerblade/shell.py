# -*- coding: utf-8 -*-
__all__ = ('Shell', 'CompletedProcess', 'CalledProcessError')

import typing
from typing import Dict, Sequence, Optional, overload, List, Mapping, Union
from typing_extensions import Literal
import shlex

from loguru import logger
import attr
import psutil

from .popen import Popen
from .stopwatch import Stopwatch
from .exceptions import (CalledProcessError, EnvNotFoundError,
                         ContainerFileNotFound)

if typing.TYPE_CHECKING:
    from .container import Container


@attr.s(auto_attribs=True, frozen=True)
class CompletedProcess:
    """Stores the result of a completed process.

    Attributes
    ----------
    args: str
        The arguments that were used to launch the process.
    returncode: int
        The returncode that was produced by the process.
    duration: float
        The number of seconds taken to complete the process.
    output: T, optional
        The output, if any, that was produced by the process.
    """
    args: str
    returncode: int
    duration: float
    output: Optional[Union[str, bytes]]

    def check_returncode(self) -> None:
        """Raises a CalledProcessError if returncode is non-zero.

        Raises
        ------
        CalledProcessError
            If the return code is non-zero.
        """
        if self.returncode != 0:
            raise CalledProcessError(cmd=self.args,
                                     returncode=self.returncode,
                                     duration=self.duration,
                                     output=self.output)


@attr.s(eq=False, hash=False, slots=True)
class Shell:
    """Provides shell access to a Docker container.
    Do not directly call the constructor to create shells. Instead, use the
    :method:`shell` method of :class:`Container` to build a shell.

    Attributes
    ----------
    container: Container
        The container to which the shell is attached.
    path: str
        The absolute path to the binary (inside the container) that should be
        used to provide this shell.
    _sources: Sequence[str]
        A sequence of files, given by their absolute paths, that should be
        sourced by the shell upon construction.
    _environment: Mapping[str, str]
        A mapping from the names of environment variables to their values.

    Raises
    ------
    ContainerFileNotFound
        If a given source file is not found.
    """
    container: 'Container' = attr.ib()
    path: str = attr.ib()
    _sources: Sequence[str] = attr.ib(factory=tuple)
    _environment: Mapping[str, str] = attr.ib(factory=dict)

    def __attrs_post_init__(self) -> None:
        object.__setattr__(self, '_sources', tuple(self._sources))
        object.__setattr__(self, '_environment', dict(self._environment))

        if self._sources:
            filesystem = self.container.filesystem()
            for src in self._sources:
                if not filesystem.isfile(src):
                    raise ContainerFileNotFound(container_id=self.container.id,
                                                path=src)

            command = ' && '.join([f'. {src} > /dev/null 2> /dev/null' for src in self._sources])  # noqa
            command += ' && env'
        else:
            command = 'env'

        # store the state of the environment
        env: Dict[str, str] = {}
        env_output = self.check_output(command, text=True)
        for env_line in env_output.replace('\r', '').split('\n'):
            name, separator, value = env_line.partition('=')
            env[name] = value

        # ignore the PWD variable
        if 'PWD' in env:
            del env['PWD']

        object.__setattr__(self, '_environment', env)

    def _local_to_host_pid(self, pid_local: int) -> Optional[int]:
        """Finds the host PID for a process inside this shell.

        Parameters
        ----------
        pid_local: int
            The PID of the process inside the container.

        Returns
        -------
        int
            The PID of the same process on the host machine.
        """
        container = self.container
        ctr_pids = [container.pid]
        info = container._info
        ctr_pids += \
            [container._exec_id_to_host_pid(i) for i in info['ExecIDs']]

        # obtain a list of all processes inside this container
        ctr_procs: List[psutil.Process] = []
        for pid in ctr_pids:
            proc = psutil.Process(pid)
            ctr_procs.append(proc)
            ctr_procs += proc.children(recursive=True)

        # read /proc/PID/status to find the namespace mapping
        for proc in ctr_procs:
            fn_proc = f'/proc/{proc.pid}/status'
            with open(fn_proc, 'r') as fh_proc:
                lines = filter(lambda l: l.startswith('NSpid'),
                               fh_proc.readlines())
                for line in lines:
                    proc_host_pid, proc_local_pid = \
                        [int(p) for p in line.strip().split('\t')[1:3]]
                    if proc_local_pid == pid_local:
                        return proc_host_pid

        return None

    def _instrument(self,
                    command: str,
                    *,
                    time_limit: Optional[int] = None,
                    kill_after: int = 1
                    ) -> str:
        q = shlex.quote
        logger.debug(f"instrumenting command: {command}")
        command = f'{self.path} -c {q(command)}'
        if time_limit:
            command = (f'timeout --kill-after={kill_after} '
                       f'--signal=SIGTERM {time_limit} {command}')
        logger.debug(f"instrumented command: {command}")
        return command

    def send_signal(self, pid: int, sig: int) -> None:
        # FIXME run as root!
        logger.debug(f"sending signal {sig} to process {pid}")
        cmd = f'kill -{sig} {pid}'
        self.run(cmd)

    def environ(self, var: str) -> str:
        """Reads the value of a given environment variable inside this shell.

        Raises
        ------
        EnvNotFoundError
            if no environment variable exists with the given name.
        """
        try:
            return self._environment[var]
        except KeyError as exc:
            raise EnvNotFoundError(var) from exc

    def check_call(self,
                   args: str,
                   *,
                   cwd: str = '/',
                   time_limit: Optional[int] = None,
                   kill_after: int = 1
                   ) -> None:
        """Executes a given commands, blocks until its completion, and checks
        that the return code is zero.

        Raises
        ------
        CalledProcessError
            If the command produced a non-zero return code.
        """
        self.run(args, stdout=False, cwd=cwd).check_returncode()

    @overload
    def check_output(self,
                     args: str,
                     *,
                     stderr: bool = True,
                     cwd: str = '/',
                     encoding: str = 'utf-8',
                     text: Literal[False],
                     time_limit: Optional[int] = None,
                     kill_after: int = 1
                     ) -> bytes:
        ...

    @overload
    def check_output(self,
                     args: str,
                     *,
                     stderr: bool = True,
                     cwd: str = '/',
                     encoding: str = 'utf-8',
                     text: Literal[True],
                     time_limit: Optional[int] = None,
                     kill_after: int = 1
                     ) -> str:
        ...

    def check_output(self,
                     args: str,
                     *,
                     stderr: bool = False,
                     cwd: str = '/',
                     encoding: str = 'utf-8',
                     text: bool = True,
                     time_limit: Optional[int] = None,
                     kill_after: int = 1
                     ) -> Union[str, bytes]:
        """Executes a given commands, blocks until its completion, and checks
        that the return code is zero.

        Returns
        -------
        str
            The output of the command execution.

        Raises
        ------
        CalledProcessError
            If the command produced a non-zero return code.
        """
        result = self.run(args,
                          encoding=encoding,
                          text=text,
                          stdout=True,
                          stderr=stderr,
                          cwd=cwd)
        result.check_returncode()
        assert result.output is not None
        return result.output

    def run(self,
            args: str,
            *,
            encoding: str = 'utf-8',
            cwd: str = '/',
            text: bool = True,
            stdout: bool = True,
            stderr: bool = False,
            time_limit: Optional[int] = None,
            kill_after: int = 1
            ) -> CompletedProcess:
        """Executes a given command and blocks until its completion.

        Parameters
        ----------
        args: str
            The command that should be executed.
        encoding: str
            The encoding that should be used for decoding, if the output of
            the process is text rather than binary.
        cwd: str
            The absolute path of the directory in the container where this
            command should be executed.
        text: bool
            If :code:`True`, the output of the process is decoded to a string
            using the provided :param:`encoding`. If :code:`False`, the output
            of the process will be treated as binary.
        stderr: bool
            If :code:`True`, the stderr will be included in the output.
        stdout: bool
            If :code:`True`, the stdout will be included in the output.
        time_limit: int, optional
            The maximum number of seconds that the command is allowed to run
            before being terminated via SIGTERM. If unspecified, no time limit
            will be imposed on command execution.
        kill_after: int
            The maximum number of seconds to wait before sending SIGKILL to
            the process after attempting termination via SIGTERM. Only applies
            when :code:`time_limit` is specified.

        Returns
        -------
        CompletedProcess
            A summary of the outcome of the command execution.
        """
        logger.debug(f"executing command: {args}")
        no_output = not stdout and not stderr
        docker_container = self.container._docker
        args_instrumented = self._instrument(args,
                                             time_limit=time_limit,
                                             kill_after=kill_after)
        with Stopwatch() as timer:
            retcode, output_bin = docker_container.exec_run(
                args_instrumented,
                detach=False,
                environment=self._environment,
                tty=True,
                stream=False,
                socket=False,
                stderr=False if no_output else stderr,  # BUG #25
                stdout=True if no_output else stdout,  # BUG #25
                workdir=cwd)

        logger.debug(f"retcode: {retcode}")

        output: Optional[Union[str, bytes]]
        if no_output:
            output = None
        elif text:
            output = output_bin.decode(encoding).rstrip('\r\n')
        else:
            output = output_bin

        result = CompletedProcess(args=args,
                                  returncode=retcode,
                                  duration=timer.duration,
                                  output=output)
        logger.debug(f"executed command: {result}")
        return result

    def popen(self,
              args: str,
              *,
              cwd: str = '/',
              encoding: Optional[str] = 'utf-8',
              stdout: bool = True,
              stderr: bool = False,
              time_limit: Optional[int] = None,
              kill_after: int = 1
              ) -> Popen:
        docker_api = self.container.daemon.api
        args_instrumented = self._instrument(args,
                                             time_limit=time_limit,
                                             kill_after=kill_after)
        exec_response = docker_api.exec_create(self.container.id,
                                               args_instrumented,
                                               environment=self._environment,
                                               tty=True,
                                               workdir=cwd,
                                               stdout=stdout,
                                               stderr=stderr)
        exec_id = exec_response['Id']
        exec_stream = docker_api.exec_start(exec_id,
                                            stream=True)
        logger.debug(f'started Exec [{exec_id}] for Popen')
        return Popen(args=args,
                     cwd=cwd,
                     container=self.container,
                     docker_api=docker_api,
                     exec_id=exec_id,
                     encoding=encoding,
                     stream=exec_stream)
