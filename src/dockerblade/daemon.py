__all__ = ("DockerDaemon",)

from collections.abc import Mapping
from types import TracebackType
from typing import Any

import attr
import docker
from loguru import logger

from .container import Container


@attr.s(frozen=True)
class DockerDaemon:
    """Maintains a connection to a Docker daemon."""
    url: str | None = attr.ib(default=None)
    client: docker.DockerClient = \
        attr.ib(init=False, eq=False, hash=False, repr=False)
    api: docker.APIClient = \
        attr.ib(init=False, eq=False, hash=False, repr=False)

    def __attrs_post_init__(self) -> None:
        client = docker.DockerClient(self.url)
        api = client.api
        object.__setattr__(self, "client", client)
        object.__setattr__(self, "api", api)
        logger.debug(f"created daemon connection: {self}")

    def __enter__(self) -> "DockerDaemon":
        return self

    def __exit__(self,
                 ex_type: type[BaseException] | None,
                 ex_val: BaseException | None,
                 ex_tb: TracebackType | None,
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
                  command: str | None = None,
                  *,
                  entrypoint: str | None = None,
                  environment: Mapping[str, str] | None = None,
                  network_mode: str = "bridge",
                  name: str | None = None,
                  ports: Mapping[int, int] | None = None,
                  user: str | None = None,
                  volumes: Mapping[str, Any] | None = None,
                  ) -> Container:
        """Creates a Docker container from a given image.

        Arguments:
        ---------
        image: str
            The name of the Docker image that should be used.
        command: str
            The command that should be run inside the container. If no
            command is given, the default command for the Docker image will
            be used instead.
        name: str, optional
            The name that should be given to the Docker container. If no name
            is given, Docker will automatically generate one instead.
        user: str, optional
            The user that should be used by the container. If none is given,
            the default user for that container image will be used.
        entrypoint: str, optional
            The entrypoint that should be used by the container. If none is
            given, the default entrypoint for the image will be used.
        environment: Mapping[str, str], optional
            An optional set of additional environment variables, indexed by
            name, that should be used by the system.
        volumes: Mapping[str, str], optional
            An optional set of volumes that should be mounted inside the
            container, specified as a dictionary where keys represent a host
            path or volume name, and values are a dictionary containing
            the following keys: :code:`bind`, the path to mount the volume
            inside the container, and :code:`mode`, specifies whether the
            mount should be read-write :code:`rw` or read-only :code:`ro`.
        ports: Mapping[int, int], optional
            An optional dictionary specifying port mappings between the host
            and container, where keys represent container ports and values
            represent host ports.
        network_mode: str
            Specifies the networking mode that should be used by the
            container. Can be either :code:`bridge`, :code`none`,
            :code:`container:<name|id>`, or :code:`host`.

        Returns:
        -------
        Container
            An interface to the newly launched container.
        """
        logger.debug(f"provisioning container for image [{image}]")
        docker_container = \
            self.client.containers.run(image,
                                       command=command,
                                       stdin_open=True,
                                       detach=True,
                                       name=name,
                                       entrypoint=entrypoint,
                                       environment=environment,
                                       ports=ports,
                                       user=user,
                                       volumes=volumes,
                                       network_mode=network_mode)
        container = self.attach(docker_container.id)
        logger.debug(f"provisioned container [{container}]"
                     f" for image [{image}]")
        return container
