# -*- coding: utf-8 -*-
__all__ = ('DockerDaemon',)

import attr
import docker


@attr.s(frozen=True)
class DockerDaemon:
    """Maintains a connection to a Docker daemon."""
    url: str = attr.ib(default='unix://var/run/docker.sock')
    client: docker.DockerClient = \
        attr.ib(init=False, eq=False, cmp=False, repr=False)
    api: docker.APIClient = \
        attr.ib(init=False, eq=False, cmp=False, repr=False)

    def __attrs_post_init__(self) -> None:
        docker_api = docker.APIClient(self.url)
        docker_client = docker.DockerClient(self.url)
        object.__setattr__(self, 'client', client)
        object.__setattr__(self, 'api', api)
