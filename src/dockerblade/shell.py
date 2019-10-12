# -*- coding: utf-8 -*-
__all__ = ('Shell', 'ShellFactory')

from typing import Tuple

import attr
import docker


class Shell:
    """Provides shell access to a Docker container."""
    @staticmethod
    def for_container(name_or_uid: str) -> 'Shell':
        # get low-level API
        # get Docker client
        # determine container PID
        raise NotImplementedError

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


@attr.s(slots=True)
class ShellFactory:
    """Used to construct shells."""
    docker_url: str = attr.ib()
    _docker_api: docker.APIClient = \
        attr.ib(init=False, repr=False, cmp=False)
    _docker_client: docker.Client = \
        attr.ib(init=False, repr=False, cmp=False)

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
