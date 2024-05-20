from __future__ import annotations

__all__ = ("Container",)

import typing as t

import attr

from .files import FileSystem
from .shell import Shell

if t.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from types import TracebackType
    from typing import Any

    from docker.models.containers import Container as DockerContainer

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
    daemon: DockerDaemon = attr.ib()
    _docker: DockerContainer = \
        attr.ib(repr=False, eq=False, hash=False)
    id: str = attr.ib(init=False, repr=True)
    name: str | None = attr.ib(init=False, repr=False)
    pid: int = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        object.__setattr__(self, "id", self._docker.id)
        object.__setattr__(self, "name", self._docker.name)
        object.__setattr__(self, "pid", int(self._info["State"]["Pid"]))

    @property
    def _info(self) -> Mapping[str, Any]:
        """Retrieves information about this container from Docker."""
        info: dict[str, Any] = self.daemon.api.inspect_container(self.id)
        assert isinstance(info, dict)
        return info

    def _exec_id_to_host_pid(self, exec_id: str) -> int:
        """Returns the host PID for a given exec command in this container."""
        pid: int = self.daemon.api.exec_inspect(exec_id)["Pid"]
        assert isinstance(pid, int)
        return pid

    def shell(self,
              path: str = "/bin/sh",
              *,
              sources: Sequence[str] | None = None,
              environment: Mapping[str, str] | None = None,
              ) -> Shell:
        """Constructs a shell for this Docker container."""
        if not environment:
            environment = {}
        if not sources:
            sources = ()
        return Shell(
            self,
            path,
            sources=sources,
            environment=environment,
        )

    def filesystem(self) -> FileSystem:
        """Provides access to the filesystem for this container."""
        return FileSystem(self, self.shell())

    def remove(self, *, force: bool = True) -> None:
        """Removes this Docker container."""
        self._docker.remove(force=force)

    def persist(
        self,
        repository: str | None = None,
        tag: str | None = None,
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
        id_: str = self._docker.commit(repository, tag).id
        assert isinstance(id_, str)
        return id_

    @property
    def ip_address(self) -> str | None:
        """The local IP address, if any, assigned to this container.

        If the container uses the host network mode, 127.0.0.1 (i.e., localhost)
        will be assigned as the ip_address of this container.
        """
        info = self._info
        if info["HostConfig"]["NetworkMode"] == "host":
            return "127.0.0.1"
        ip_address: str | None = info["NetworkSettings"].get("IPAddress", None)
        return ip_address

    @property
    def network_mode(self) -> str:
        """The network mode used by this container."""
        mode: str = self._info["HostConfig"]["NetworkMode"]
        assert isinstance(mode, str)
        return mode

    def __enter__(self) -> t.Self:
        return self

    def __exit__(self,
                 ex_type: type[BaseException] | None,
                 ex_val: BaseException | None,
                 ex_tb: TracebackType | None,
                 ) -> None:
        self.remove()
