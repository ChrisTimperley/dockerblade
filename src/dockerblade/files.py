# -*- coding: utf-8 -*-
__all__ = ('FileSystem',)


from .daemon import DockerDaemon


@attr.s(eq=False, hash=False)
class FileSystem:
    """Provides access to a Docker filesystem."""
    daemon: DockerDaemon = attr.ib(factory=DockerDaemon)
