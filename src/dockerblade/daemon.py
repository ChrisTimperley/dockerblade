# -*- coding: utf-8 -*-
__all__ = ('DockerDaemon',)

from types import TracebackType
from typing import Dict, Optional, Type

from loguru import logger
import attr
import docker

from .container import Container


@attr.s(frozen=True)
class DockerDaemon:
    """Maintains a connection to a Docker daemon."""
    url: str = attr.ib(default='unix://var/run/docker.sock')
    client: docker.DockerClient = \
        attr.ib(init=False, eq=False, hash=False, repr=False)
    api: docker.APIClient = \
        attr.ib(init=False, eq=False, hash=False, repr=False)

    def __attrs_post_init__(self) -> None:
        api = docker.APIClient(self.url)
        client = docker.DockerClient(self.url)
        object.__setattr__(self, 'client', client)
        object.__setattr__(self, 'api', api)
        logger.debug(f"created daemon connection: {self}")

    def __enter__(self) -> 'DockerDaemon':
        return self

    def __exit__(self,
                 ex_type: Optional[Type[BaseException]],
                 ex_val: Optional[BaseException],
                 ex_tb: Optional[TracebackType]
                 ) -> None:
        self.close()

    def close(self) -> None:
        logger.debug(f"closing daemon connection: {self}")
        self.api.close()
        self.client.close()
        logger.debug(f"closed daemon connection: {self}")

    def attach(self, id_or_name: str) -> Container:
        """Attaches to a running Docker with a given ID or name."""
        logger.debug(f"attaching to container with ID or name [{id_or_name}]")
        docker_container = self.client.containers.get(id_or_name)
        container = Container(daemon=self, docker=docker_container)
        logger.debug(f"attached to container [{container}]")
        return container

    def provision(self,
                  image: str,
                  *,
                  volumes: Optional[Dict[str, str]] = None
                  ) -> Container:
        """Creates a Docker container from a given image.

        Arguments
        ---------
        image: str
            The name of the Docker image that should be used.
        volumes: Dict[str, str], optional
            An optional set of volumes that should be mounted inside the
            container, specified as a dictionary where keys represent a host
            path or volume name, and values are a dictionary containing
            the following keys: :code:`bind`, the path to mount the volume
            inside the container, and :code:`mode`, specifies whether the
            mount should be read-write :code:`rw` or read-only :code:`ro`.

        Returns
        -------
        Container
            An interface to the newly launched container.
        """
        logger.debug(f"provisioning container for image [{image}]")
        docker_container = \
            self.client.containers.run(image,
                                       stdin_open=True,
                                       detach=True,
                                       volumes=volumes)
        container = self.attach(docker_container.id)
        logger.debug(f"provisioned container [{container}]"
                     f" for image [{image}]")
        return container
