# -*- coding: utf-8 -*-
import pytest

from contextlib import ExitStack

import dockerblade


def test_persist(daemon):
    with ExitStack() as exit_stack:
        daemon = dockerblade.DockerDaemon()
        exit_stack.push(daemon)

        container = daemon.provision('alpine:3.10')
        exit_stack.callback(container.remove)

        files = container.filesystem()
        files.write('/tmp/foo', 'hello world')

        image_id = container.persist()
        try:
            assert daemon.client.images.get(image_id)
        finally:
            daemon.client.images.remove(image_id)
