# -*- coding: utf-8 -*-
import pytest

import os
import shutil
import tempfile

from common import alpine_310

from dockerblade import exceptions as exc


def test_write(alpine_310):
    files = alpine_310.filesystem()

    # write to new file
    expected = 'hello world'
    files.write('/tmp/foo', expected)
    assert files.isfile('/tmp/foo')
    assert files.read('/tmp/foo') == expected

    # overwrite existing file
    expected = 'goodbye world'
    files.write('/tmp/foo', expected)
    assert files.read('/tmp/foo') == expected
    files.remove('/tmp/foo')

    # write to a file that belongs to a non-existent directory
    with pytest.raises(exc.ContainerFileNotFound):
        files.write('/tmp/bar/bork', 'code things')


def test_tempfile(alpine_310):
    files = alpine_310.filesystem()
    filename: str
    with files.tempfile() as filename:
        assert files.isfile(filename)
    assert not files.exists(filename)


def test_remove(alpine_310):
    files = alpine_310.filesystem()

    filename = files.mktemp()
    assert files.isfile(filename)
    files.remove(filename)
    assert not files.exists(filename)

    # remove non-existent file
    with pytest.raises(exc.ContainerFileNotFound):
        files.remove(filename)

    # remove directory
    assert files.isdir('/bin')
    with pytest.raises(exc.IsADirectoryError):
        files.remove('/bin')
    assert files.isdir('/bin')


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


def test_makedirs(alpine_310):
    files = alpine_310.filesystem()

    # parent directory exists
    files.makedirs('/tmp/foo')
    assert files.isdir('/tmp/foo')
    files.makedirs('/tmp/foo/bar')
    assert files.isdir('/tmp/foo/bar')

    # intermediate directory doesn't exist
    files.makedirs('/tmp/bar/foo')
    assert files.isdir('/tmp/bar/foo')

    # directory already exists
    with pytest.raises(exc.ContainerFileAlreadyExists):
        files.makedirs('/bin')
    assert files.isdir('/bin')
    files.makedirs('/bin', exist_ok=True)

    # path is a file
    with pytest.raises(exc.ContainerFileAlreadyExists):
        files.makedirs('/bin/cp')
    with pytest.raises(exc.ContainerFileAlreadyExists):
        files.makedirs('/bin/dd', exist_ok=True)

    # parent directory is a file
    with pytest.raises(exc.IsNotADirectoryError):
        files.makedirs('/bin/cp/foo')
    assert not files.exists('/bin/cp/foo')
    assert not files.isdir('/bin/cp')
    assert files.isfile('/bin/cp')


def test_mktemp(alpine_310):
    files = alpine_310.filesystem()

    # create a temporary file
    fn = files.mktemp()
    assert files.isfile(fn)
    assert os.path.isabs(fn)
    assert fn.startswith('/tmp/')

    # use specified dir
    d = '/boop'
    files.makedirs(d, exist_ok=True)
    assert files.isdir(d)
    fn = files.mktemp(dirname=d)
    assert os.path.dirname(fn) == d
    assert files.isfile(fn)

    # use non-existent dir
    with pytest.raises(exc.ContainerFileNotFound):
        d = '/idontexist'
        assert not files.isdir(d)
        files.mktemp(dirname=d)

    # add suffix
    fn = files.mktemp(suffix='.foo')
    assert fn.endswith('.foo')
    assert files.isfile(fn)

    # add prefix
    fn = files.mktemp(prefix='foo')
    assert os.path.basename(fn).startswith('foo')
    assert files.isfile(fn)


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


def test_copy_from_host(alpine_310):
    shell = alpine_310.shell()
    files = alpine_310.filesystem()

    content = 'hello world'
    try:
        _, fn_host = tempfile.mkstemp()
        with open(fn_host, 'w') as fh:
            fh.write(content)

        # copy to non-existent directory
        with pytest.raises(exc.ContainerFileNotFound):
            files.copy_from_host(fn_host, '/temp/foo')

        # copy file
        files.copy_from_host(fn_host, '/tmp/foo')
        assert files.read('/tmp/foo') == content
    finally:
        os.remove(fn_host)

    # copy non-existent file from host
    assert not os.path.exists(fn_host)
    with pytest.raises(exc.HostFileNotFound):
        files.copy_from_host(fn_host, '/tmp/bar')

    # copy directory
    try:
        dir_host = tempfile.mkdtemp()

        fn_bar = os.path.join(dir_host, 'bar')
        with open(fn_bar, 'w') as fh:
            fh.write(content)

        fn_foo = os.path.join(dir_host, 'foo')
        with open(fn_foo, 'w') as fh:
            fh.write(content)

        files.copy_from_host(dir_host, '/tmp/foobardir')
        assert files.exists('/tmp/foobardir')
        assert files.exists('/tmp/foobardir/foo')
        assert files.exists('/tmp/foobardir/bar')
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
