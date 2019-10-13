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


def test_run(alpine_310, shell_factory):
    shell = shell_factory.build(alpine_310.id, '/bin/sh')
    result = shell.run("echo 'hello world'")
    assert result.returncode == 0
    assert result.output == 'hello world'


def test_output(alpine_310, shell_factory):
    shell = shell_factory.build(alpine_310.id, '/bin/sh')
    output = shell.check_output("echo 'hello world'")
    assert output == 'hello world'
