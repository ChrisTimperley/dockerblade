# -*- coding: utf-8 -*-
__all__ = ('DockerDaemon',)

import attr
import docker


@attr.s(frozen=True)
class DockerDaemon:
    """Maintains a connection to a Docker daemon."""
    url: str = attr.ib()
    client: docker.DockerClient = \
        attr.ib(init=False, eq=False, cmp=False, repr=False)
    api: docker.APIClient = \
        attr.ib(init=False, eq=False, cmp=False, repr=False)
