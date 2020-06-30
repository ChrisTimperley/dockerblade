# -*- coding: utf-8 -*-
import pytest

from contextlib import ExitStack
import tempfile

import dockerblade


def test_host_network_mode(daemon):
    with ExitStack() as exit_stack:
        container = daemon.provision('alpine:3.10', network_mode='host')
        exit_stack.callback(container.remove)
        assert container.network_mode == 'host'
        assert container.ip_address == '127.0.0.1'

        container = daemon.provision('alpine:3.10')
        exit_stack.callback(container.remove)
        assert container.network_mode == 'bridge'
        assert container.ip_address != '127.0.0.1'


def test_name(daemon):
    with ExitStack() as exit_stack:
        name = 'foobar'
        container = daemon.provision('alpine:3.10', name=name)
        exit_stack.callback(container.remove)
        assert container.name == name


def test_environment(daemon):
    with ExitStack() as exit_stack:
        env_var = 'FOO'
        env_val = 'FOOBARBAZ'
        env = {env_var: env_val}
        container = daemon.provision('alpine:3.10', environment=env)
        exit_stack.callback(container.remove)
        shell = container.shell()
        assert shell.environ(env_var) == env_val


def test_readonly_volume(daemon):
    with ExitStack() as exit_stack:
        expected = 'Hello!'
        _, mount_from = tempfile.mkstemp()
        with open(mount_from, 'w') as fh:
            fh.write(expected)

        mount_to = '/foo'
        volumes = {mount_from: {'mode': 'rw', 'bind': mount_to}}
        container = daemon.provision('alpine:3.10', volumes=volumes)
        exit_stack.callback(container.remove)

        files = container.filesystem()

        # check that file is mounted
        assert files.read(mount_to) == expected

        # #55 move to test_readwrite_volume
        # check that changes are reflected on host
        # expected = 'Goodbye!'
        # files.write(mount_to, expected)
        # assert open(mount_from, 'r').read() == expected
