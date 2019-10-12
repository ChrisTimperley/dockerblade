# -*- coding: utf-8 -*-
__all__ = ('Shell', 'ShellFactory')

from typing import Tuple

from loguru import logger
from docker.models.containers import Container as DockerContainer
import attr
import docker


@attr.s(cmp=False)
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

    def environ(self, var: str) -> str:
        """Reads the value of a given environment variable inside this shell.

        Raises
        ------
        EnvNotFoundError
            if no environment variable exists with the given name.
        """
        raise NotImplementedError

    def execute(self, command: str) -> Tuple[int, str, float]:
        """Executes a given command and blocks until its completion.

        Returns
        -------
        Tuple[int, str, float]
            The return code, output, and wall-clock running time of the
            execution, measured in seconds.
        """
        raise NotImplementedError


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
        attr.ib(init=False, repr=False, cmp=False)
    _docker_client: docker.DockerClient = \
        attr.ib(init=False, repr=False, cmp=False)

    def __attrs_post_init__(self) -> None:
        docker_api = docker.APIClient(self.docker_url)
        docker_client = docker.Client(self.docker_url)
        object.__setattr__(self, '_docker_api', docker_api)
        object.__setattr__(self, '_docker_client', docker_api)

    def __enter__(self) -> 'ShellFactory':
        return self

    def __exit__(self, ex_type, ex_val, ex_tb) -> None:
        self.close()

    def close(self) -> None:
        logger.debug("closing shell factory: %s", self)
        self._docker_api.close()
        self._docker_client.close()
        logger.debug("closed shell factory: %s", self)

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
        logger.debug("building shell [%s] for container [%s]", path, name)
        container = self._docker_client.containers.get(name)
        shell = Shell(container_name=name,
                      path=path,
                      container=container,
                      docker_api=self._docker_api)
        logger.debug("built shell for container: %s", shell)
        return shell
