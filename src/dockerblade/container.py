# -*- coding: utf-8 -*-
__all__ = ('Container',)

from types import TracebackType
import typing
from typing import Any, Mapping, Optional, Sequence, Type

import attr
from docker.models.containers import Container as DockerContainer

from .shell import Shell
from .files import FileSystem

if typing.TYPE_CHECKING:
    from .daemon import DockerDaemon


@attr.s(slots=True, frozen=True)
class Container:
    """Provides access to a Docker container.

    Attributes
    ----------
    daemon: DockerDaemon
        Provides access to the Docker daemon that manages this container.
    id: str
        The unique ID of the container.
    pid: int
        The PID of the container process on the host machine.
    name: str, optional
        The name, if any, assigned to the container.
    """
    daemon: 'DockerDaemon' = attr.ib()
    _docker: DockerContainer = \
        attr.ib(repr=False, eq=False, hash=False)
    id: str = attr.ib(init=False, repr=True)
    name: Optional[str] = attr.ib(init=False, repr=False)
    pid: int = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        object.__setattr__(self, 'id', self._docker.id)
        object.__setattr__(self, 'name', self._docker.name)
        object.__setattr__(self, 'pid', int(self._info['State']['Pid']))

    @property
    def _info(self) -> Mapping[str, Any]:
        """Retrieves information about this container from Docker."""
        return self.daemon.api.inspect_container(self.id)

    def _exec_id_to_host_pid(self, exec_id: str) -> int:
        """Returns the host PID for a given exec command in this container."""
        return self.daemon.api.exec_inspect(exec_id)['Pid']

    def shell(self,
              path: str = '/bin/sh',
              *,
              sources: Optional[Sequence[str]] = None,
              environment: Optional[Mapping[str, str]] = None
              ) -> Shell:
        """Constructs a shell for this Docker container."""
        if not environment:
            environment = {}
        if not sources:
            sources = tuple()
        return Shell(self, path, sources=sources, environment=environment)

    def filesystem(self) -> FileSystem:
        """Provides access to the filesystem for this container."""
        return FileSystem(self, self.shell())

    def remove(self, force: bool = True) -> None:
        """Removes this Docker container."""
        self._docker.remove(force=force)

    def persist(self,
                repository: Optional[str] = None,
                tag: Optional[str] = None
                ) -> str:
        """Persists this container to an image.

        Parameters
        ----------
        repository: str, optional
            The name of the repository to which the image should belong.
        tag: str, optional
            The tag that should be used for the image.

        Returns
        -------
        str
            The ID of the generated image.
        """
        return self._docker.commit(repository, tag).id

    @property
    def ip_address(self) -> Optional[str]:
        """The local IP address, if any, assigned to this container. If the
        container uses the host network mode, 127.0.0.1 (i.e., localhost) will
        be assigned as the ip_address of this container.
        """
        info = self._info
        if info['HostConfig']['NetworkMode'] == 'host':
            return '127.0.0.1'
        else:
            return info['NetworkSettings'].get('IPAddress', None)

    @property
    def network_mode(self) -> str:
        """The network mode used by this container."""
        return self._info['HostConfig']['NetworkMode']

    def __enter__(self) -> 'Container':
        return self

    def __exit__(self,
                 ex_type: Optional[Type[BaseException]],
                 ex_val: Optional[BaseException],
                 ex_tb: Optional[TracebackType]
                 ) -> None:
        self.remove()
