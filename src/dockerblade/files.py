# -*- coding: utf-8 -*-
__all__ = ('FileSystem',)


from .shell import Shell
from .daemon import DockerDaemon


@attr.s(slots=True, eq=False, hash=False, repr=False)
class FileSystem:
    """Provides access to a Docker filesystem.
    
    Attributes
    ----------
    container_name: str
        The name of the container to which the filesystem belongs.
    """
    _daemon: DockerDaemon = attr.ib(factory=DockerDaemon)
    _shell: Shell = attr.ib(init=False)

    @property
    def container_name(self) -> str:
        return self._shell.container_name

    def __repr__(self) -> str:
        return f'FileSystem(container_name={self.container_name})'
