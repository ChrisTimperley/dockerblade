# -*- coding: utf-8 -*-
from contextlib import ExitStack

import pytest
import docker

import dockerblade
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


def test_check_output(alpine_310, shell_factory):
    shell = shell_factory.build(alpine_310.id, '/bin/sh')
    t = shell.check_output
    b = lambda c: t(c, text=False).decode('utf-8').rstrip('\r\n')
    assert t("echo 'hello world'") == 'hello world'
    assert b("echo 'hello world'") == 'hello world'


def test_check_call(alpine_310, shell_factory):
    shell = shell_factory.build(alpine_310.id, '/bin/sh')
    shell.check_output("exit 0")
    with pytest.raises(dockerblade.exceptions.CalledProcessError):
        shell.check_output("exit 1")


def test_popen(alpine_310, shell_factory):
    shell = shell_factory.build(alpine_310.id, '/bin/sh')
    p = shell.popen("echo 'hello world'")
    assert p.wait() == 0
    assert p.returncode == 0

    p = shell.popen("sleep 5 && exit 1")
    with pytest.raises(dockerblade.exceptions.TimeoutExpired):
        p.wait(1)
    assert p.wait(8) == 1
