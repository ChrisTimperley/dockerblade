# -*- coding: utf-8 -*-
from contextlib import ExitStack
import subprocess
import time

import pytest
import docker

import dockerblade
from dockerblade import Shell, DockerDaemon


@pytest.fixture
def alpine_310():
    with ExitStack() as exit_stack:
        daemon = DockerDaemon()
        exit_stack.push(daemon)

        docker_client = daemon.client
        docker_container = \
            docker_client.containers.run('alpine:3.10', stdin_open=True, detach=True)
        container = daemon.attach(docker_container.id)
        exit_stack.callback(container.remove)
        yield container


def test_run(alpine_310):
    shell = alpine_310.shell('/bin/sh')
    result = shell.run("echo 'hello world'")
    assert result.returncode == 0
    assert result.output == 'hello world'


def test_check_output(alpine_310):
    shell = alpine_310.shell('/bin/sh')
    t = shell.check_output
    b = lambda c: t(c, text=False).decode('utf-8').rstrip('\r\n')
    assert t("echo 'hello world'") == 'hello world'
    assert b("echo 'hello world'") == 'hello world'
    assert t('NAME="cool" && echo "${NAME}"') == 'cool'
    assert t('echo "${PWD}"', cwd='/tmp') == '/tmp'
    assert t('echo "${PATH}"') == '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'


def test_check_call(alpine_310):
    shell = alpine_310.shell('/bin/sh')
    shell.check_output("exit 0")
    with pytest.raises(dockerblade.exceptions.CalledProcessError):
        shell.check_output("exit 1")


def test_environ(alpine_310):
    shell = alpine_310.shell('/bin/sh')
    assert shell.environ('PATH') == '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'


def test_popen(alpine_310):
    shell = alpine_310.shell('/bin/sh')
    id_container = shell.container.id
    p = shell.popen("echo 'hello world'")
    assert p.wait() == 0
    assert p.returncode == 0

    p = shell.popen("sleep 60 && exit 1")
    with pytest.raises(dockerblade.exceptions.TimeoutExpired):
        p.wait(1)
    p.kill()
    assert p.wait(1.5) != 0
