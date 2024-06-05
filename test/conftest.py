# -*- coding: utf-8 -*-
import pytest

import os
from contextlib import ExitStack

import dockerblade


@pytest.fixture(scope='session')
def daemon():
    url: str | None = os.environ.get("DOCKER_HOST", None)
    with dockerblade.DockerDaemon(url=url) as daemon:
        yield daemon


@pytest.fixture
def alpine_310(daemon):
    with ExitStack() as exit_stack:
        container = daemon.provision('alpine:3.10')
        exit_stack.callback(container.remove)
        yield container
