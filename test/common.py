# -*- coding: utf-8 -*-
from contextlib import ExitStack

import pytest

import dockerblade


@pytest.fixture
def alpine_310():
    with ExitStack() as exit_stack:
        daemon = dockerblade.DockerDaemon()
        exit_stack.push(daemon)

        docker_client = daemon.client
        docker_container = \
            docker_client.containers.run('alpine:3.10', stdin_open=True, detach=True)
        container = daemon.attach(docker_container.id)
        exit_stack.callback(container.remove)
        yield container
