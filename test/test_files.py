# -*- coding: utf-8 -*-
import pytest

import os
import shutil
import tempfile

from common import alpine_310

from dockerblade import exceptions as exc


def test_exists(alpine_310):
    files = alpine_310.filesystem()
    assert files.exists('/bin/sh')
    assert files.exists('/bin/cp')
    assert not files.exists('/bin/foobar')


def test_isdir(alpine_310):
    files = alpine_310.filesystem()
    assert not files.isdir('/bin/sh')
    assert files.isdir('/bin')


def test_islink(alpine_310):
    files = alpine_310.filesystem()
    assert files.islink('/sbin/arp')
    assert not files.islink('/sbin')
    assert not files.islink('/sbin/ldconfig')


def test_isfile(alpine_310):
    files = alpine_310.filesystem()
    assert files.isfile('/sbin/arp')
    assert files.isfile('/bin/sh')
    assert not files.isfile('/bin')


def test_copy_to_host(alpine_310):
    content = "hello world"
    shell = alpine_310.shell()
    files = alpine_310.filesystem()
    shell.run(f'echo "{content}" > /tmp/hello')
    _, fn_host = tempfile.mkstemp()
    try:
        files.copy_to_host('/tmp/hello', fn_host)
        with open(fn_host, 'r') as f:
            assert f.read() == (content + '\n')
    finally:
        os.remove(fn_host)

    # non-existent file
    _, fn_host = tempfile.mkstemp()
    try:
        with pytest.raises(exc.ContainerFileNotFound):
             files.copy_to_host('/foo/bar', fn_host)
    finally:
        os.remove(fn_host)

    # non-existent host directory
    fn_host = '/tmp/foo/bar/foo/bar'
    with pytest.raises(exc.HostFileNotFound):
        files.copy_to_host('/tmp/hello', fn_host)

    # copy directory
    dir_host: str = tempfile.mkdtemp()
    dir_host_periodic: str = os.path.join(dir_host, 'periodic')
    try:
        files.copy_to_host('/etc/periodic', dir_host)
        assert os.path.isdir(dir_host_periodic)
        assert set(os.listdir(dir_host_periodic)) == {
            'daily', 'weekly', '15min', 'hourly', 'monthly'}
    finally:
        shutil.rmtree(dir_host)


def test_read(alpine_310):
    files = alpine_310.filesystem()
    shell = alpine_310.shell()
    content = 'Hello world!'
    shell.run(f'echo "{content}" > /tmp/hello')

    # read file
    expected = content + '\n'
    assert files.read('/tmp/hello') == expected

    # read binary file
    binary = files.read('/tmp/hello', binary=True)
    text = binary.decode('utf-8')
    assert text == expected

    # non-existent file
    with pytest.raises(exc.ContainerFileNotFound):
        files.read('/foo/bar')

    # directory
    with pytest.raises(exc.IsADirectoryError):
        files.read('/bin')
