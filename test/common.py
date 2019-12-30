# -*- coding: utf-8 -*-
from contextlib import ExitStack

import pytest

import dockerblade


@pytest.fixture
def alpine_310():
    with ExitStack() as exit_stack:
        daemon = dockerblade.DockerDaemon()
        exit_stack.push(daemon)
        container = daemon.provision('alpine:3.10')
        exit_stack.callback(container.remove)
        yield container
