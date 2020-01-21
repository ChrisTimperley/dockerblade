# -*- coding: utf-8 -*-
__all__ = ('Container',)

import typing
from typing import Optional

import attr
from docker.models.containers import Container as DockerContainer

from .shell import Shell
from .files import FileSystem

if typing.TYPE_CHECKING:
    from .daemon import DockerDaemon


@attr.s(slots=True, frozen=True)
class Container:
    """Provides access to a Docker container."""
    daemon: 'DockerDaemon' = attr.ib()
    _docker: DockerContainer = \
        attr.ib(repr=False, eq=False, hash=False)
    id: str = attr.ib(init=False, repr=True)

    def __attrs_post_init__(self) -> None:
        object.__setattr__(self, 'id', self._docker.id)

    def shell(self, path: str = '/bin/sh') -> Shell:
        """Constructs a shell for this Docker container."""
        return Shell(self, path)

    def filesystem(self) -> FileSystem:
        """Provides access to the filesystem for this container."""
        return FileSystem(self, self.shell())

    def remove(self, force: bool = True) -> None:
        """Removes this Docker container."""
        self._docker.remove(force=force)

    @property
    def ip_address(self) -> Optional[str]:
        """The local IP address, if any, assigned to this container."""
        docker_info = self.daemon.api.inspect_container(self.id)
        return docker_info['NetworkSettings'].get('IPAddress', None)
