# -*- coding: utf-8 -*-
__all__ = ('Shell', 'CompletedProcess', 'CalledProcessError')

import typing
from typing import Tuple, Optional, Union, overload
from typing_extensions import Literal
import shlex

from loguru import logger
from docker.models.containers import Container as DockerContainer
import attr
import docker

from .popen import Popen
from .stopwatch import Stopwatch
from .exceptions import CalledProcessError, EnvNotFoundError

if typing.TYPE_CHECKING:
    from .container import Container
    from .daemon import DockerDaemon


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

@attr.s(eq=False, hash=False)
class Shell:
    """Provides shell access to a Docker container.
    Do not directly call the constructor to create shells. Instead, you
    should use a :class:`ShellFactory` to build shells.

    Attributes
    ----------
    container_name: str
        The name of the container to which the shell is attached.
    path: str
        The absolute path to the binary (inside the container) that should be
        used to provide this shell.
    """
    container: 'Container' = attr.ib()
    path: str = attr.ib()

    def _instrument(self,
                    command: str,
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
            return self.check_output(f'echo "${{{var}}}"', text=True)
        except CalledProcessError as exc:
            raise EnvNotFoundError(var) from exc

    def check_call(self,
                   args: str,
                   *,
                   cwd: str = '/'
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
                     text: Literal[False]
                     ) -> bytes:
        ...

    @overload
    def check_output(self,
                     args: str,
                     *,
                     stderr: bool = True,
                     cwd: str = '/',
                     encoding: str = 'utf-8',
                     text: Literal[True]
                     ) -> str:
        ...

    def check_output(self,
                     args: str,
                     *,
                     stderr: bool = False,
                     cwd: str = '/',
                     encoding: str = 'utf-8',
                     text: bool = True
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
            stderr: bool = False
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

        Returns
        -------
        CompletedProcess
            A summary of the outcome of the command execution.
        """
        logger.debug(f"executing command: {args}")
        no_output = not stdout and not stderr
        docker_container = self.container._docker
        args_instrumented = self._instrument(args)

        with Stopwatch() as timer:
            retcode, output_bin = docker_container.exec_run(
                args_instrumented,
                detach=False,
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
              stdout: bool = True,
              stderr: bool = False
              ) -> Popen:
        docker_api = self.container.daemon.api
        args_instrumented = self._instrument(args)
        exec_response = docker_api.exec_create(self.container.id,
                                               args_instrumented,
                                               tty=True,
                                               workdir=cwd,
                                               stdout=stdout,
                                               stderr=stderr)
        exec_id = exec_response['Id']
        exec_stream = docker_api.exec_start(exec_id, stream=True)
        return Popen(args=args,
                     cwd=cwd,
                     container=self.container,
                     docker_api=docker_api,
                     exec_id=exec_id,
                     stream=exec_stream)
