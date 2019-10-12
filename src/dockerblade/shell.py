# -*- coding: utf-8 -*-
__all__ = ('Shell', 'ShellFactory')

from typing import Tuple

import attr
import docker


class Shell:
    """Provides shell access to a Docker container.
    Do not directly call the constructor to create shells. Instead, you
    should use a :class:`ShellFactory` to build shells.
    """
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
    """Used to construct shells."""
    docker_url: str = attr.ib(default='unix://var/run/docker.sock')
    _docker_api: docker.APIClient = \
        attr.ib(init=False, repr=False, cmp=False)
    _docker_client: docker.Client = \
        attr.ib(init=False, repr=False, cmp=False)

    def __attrs_post_init__(self) -> None:
        docker_api = docker.APIClient(self.docker_url)
        docker_client = docker.Client(self.docker_url)
        object.__init__(self, '_docker_api', docker_api)
        object.__init__(self, '_docker_client', docker_api)

    def __enter__(self) -> 'ShellFactory':
        return self

    def __exit__(self, ex_type, ex_val, ex_tb) -> None:
        self.close()

    def close(self) -> None:
        self._docker_api.close()
        self._docker_client.close()

    def build(self,
              name: str,
              shell: str = '/bin/bash'
              ) -> 'Shell':
        """Constructs a shell for a given Docker container.

        Parameters
        ----------
        name: str
            The name or ID of the Docker container.
        shell: str
            The absolute path to the shell inside that container that should
            be used (e.g., :code:`/bin/bash`).

        Returns
        -------
        Shell
            A shell for the given container.
        """
        raise NotImplementedError
