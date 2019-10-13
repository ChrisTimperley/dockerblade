# -*- coding: utf-8 -*-
__all__ = ('DockerDaemon',)

from loguru import logger
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
        api = docker.APIClient(self.url)
        client = docker.DockerClient(self.url)
        object.__setattr__(self, 'client', client)
        object.__setattr__(self, 'api', api)
        logger.debug(f"created daemon connection: {self}")

    def __enter__(self) -> 'DockerDaemon':
        return self

    def __exit__(self, ex_type, ex_val, ex_tb) -> None:
        self.close()

    def close(self) -> None:
        logger.debug(f"closing daemon connection: {self}")
        self.api.close()
        self.client.close()
        logger.debug(f"closed daemon connection: {self}")
