# -*- coding: utf-8 -*-
import pytest

from contextlib import ExitStack

import dockerblade


@pytest.fixture(scope='session')
def daemon():
    with dockerblade.DockerDaemon() as daemon:
        yield daemon


@pytest.fixture
def alpine_310(daemon):
    with ExitStack() as exit_stack:
        container = daemon.provision('alpine:3.10')
        exit_stack.callback(container.remove)
        yield container
