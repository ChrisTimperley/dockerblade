# -*- coding: utf-8 -*-
__all__ = ('Container',)

import attr
from docker.models.containers import Container as DockerContainer

from .daemon import DockerDaemon


@attr.s(slots=True, frozen=True)
class Container:
    """Provides access to a Docker container."""
    id: str = attr.ib()
    daemon: DockerDaemon = attr.ib()
    _docker: DockerContainer = \
        attr.ib(init=False, repr=False, eq=False, hash=False)

    def __attrs_post_init__(self) -> None:
        docker_client = self.daemon.client
        self._docker_container = docker_client.containers.get(self.id)
