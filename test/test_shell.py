# -*- coding: utf-8 -*-
from contextlib import ExitStack

import pytest
import docker

from dockerblade import Shell, ShellFactory


@pytest.fixture
def alpine_310():
    with ExitStack() as exit_stack:
        docker_client = docker.DockerClient()
        exit_stack.callback(docker_client.close)

        container = docker_client.containers.run('alpine:3.10', stdin_open=True, detach=True)
        exit_stack.callback(container.remove, force=True)
        yield container


@pytest.fixture
def shell_factory():
    with ShellFactory() as factory:
        yield factory


def test_hello_world(alpine_310, shell_factory):
    shell = shell_factory.build(alpine_310.id, '/bin/sh')
    retcode, output, duration = shell.execute("echo 'hello world'")
    assert retcode == 0
    assert output == 'hello world'
