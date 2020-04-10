# -*- coding: utf-8 -*-
import pytest

from contextlib import ExitStack
import tempfile

import dockerblade


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
