# -*- coding: utf-8 -*-
__all__ = ('Shell', 'ShellFactory', 'CompletedProcess', 'CalledProcessError')

from typing import Tuple, Optional, Union, overload
from typing_extensions import Literal
import shlex

from loguru import logger
from docker.models.containers import Container as DockerContainer
import attr
import docker

from .popen import Popen
from .stopwatch import Stopwatch
from .exceptions import CalledProcessError


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
    container_name: str = attr.ib()
    path: str = attr.ib()
    _container: DockerContainer = attr.ib(repr=False)
    _docker_api: docker.APIClient = attr.ib(repr=False)

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
        raise NotImplementedError

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
        container = self._container
        args_instrumented = self._instrument(args)

        with Stopwatch() as timer:
            retcode, output_bin = container.exec_run(
                args_instrumented,
                stderr=stderr,
                stdout=stdout,
                workdir=cwd)

        output: Optional[Union[str, bytes]]
        if not stdout and not stderr:
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
        docker_api = self._docker_api
        args_instrumented = self._instrument(args)
        exec_response = docker_api.exec_create(self._container.id,
                                               args_instrumented,
                                               tty=True,
                                               stdout=stdout,
                                               stderr=stderr)
        exec_id = exec_response['Id']
        exec_stream = docker_api.exec_start(exec_id, stream=True)
        return Popen(args=args,
                     cwd=cwd,
                     container=self._container,
                     docker_api=docker_api,
                     exec_id=exec_id,
                     stream=exec_stream)


@attr.s(slots=True, frozen=True)
class ShellFactory:
    """Used to construct shells.

    Attributes
    ----------
    docker_url: str
        The URL of the associated Docker engine.
    """
    docker_url: str = attr.ib(default='unix://var/run/docker.sock')
    _docker_api: docker.APIClient = \
        attr.ib(init=False, repr=False, eq=False, hash=False)
    _docker_client: docker.DockerClient = \
        attr.ib(init=False, repr=False, eq=False, hash=False)

    def __attrs_post_init__(self) -> None:
        docker_api = docker.APIClient(self.docker_url)
        docker_client = docker.DockerClient(self.docker_url)
        object.__setattr__(self, '_docker_api', docker_api)
        object.__setattr__(self, '_docker_client', docker_client)

    def __enter__(self) -> 'ShellFactory':
        return self

    def __exit__(self, ex_type, ex_val, ex_tb) -> None:
        self.close()

    def close(self) -> None:
        logger.debug("closing shell factory: {}", self)
        self._docker_api.close()
        self._docker_client.close()
        logger.debug("closed shell factory: {}", self)

    def build(self,
              name: str,
              path: str = '/bin/bash'
              ) -> 'Shell':
        """Constructs a shell for a given Docker container.

        Parameters
        ----------
        name: str
            The name or ID of the Docker container.
        path: str
            The absolute path to the shell inside that container that should
            be used (e.g., :code:`/bin/bash`).

        Returns
        -------
        Shell
            A shell for the given container.
        """
        logger.debug("building shell [{}] for container [{}]", path, name)
        container = self._docker_client.containers.get(name)
        shell = Shell(container_name=name,
                      path=path,
                      container=container,
                      docker_api=self._docker_api)
        logger.debug("built shell for container: {}", shell)
        return shell
