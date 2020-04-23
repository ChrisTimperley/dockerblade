# -*- coding: utf-8 -*-
import pytest

import dockerblade


def test_run(alpine_310):
    shell = alpine_310.shell('/bin/sh')
    result = shell.run("echo 'hello world'")
    assert result.returncode == 0
    assert result.output == 'hello world'

    # see issue #25
    result = shell.run("echo 'hello world'", stderr=False, stdout=False)
    assert result.returncode == 0
    assert result.output == None


def test_bad_sources(alpine_310):
    filename = 'this-file-does-not-exist'
    with pytest.raises(dockerblade.exceptions.ContainerFileNotFound) as err:
        alpine_310.shell('/bin/sh', sources=[filename])
    assert err.value.path == filename


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
    shell.check_call('exit 0')
    with pytest.raises(dockerblade.exceptions.CalledProcessError):
        shell.check_call('exit 1')


def test_environ(alpine_310):
    shell = alpine_310.shell('/bin/sh')
    assert shell.environ('PATH') == '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'

    env = {'NAME': 'CHRIS'}
    shell = alpine_310.shell('/bin/sh', environment=env)
    assert shell.environ('NAME') == 'CHRIS'


def test_sources(alpine_310):
    # create a file that will be sourced
    files = alpine_310.filesystem()
    files.write('/tmp/source.sh', 'export NAME="dockerblade"')

    shell = alpine_310.shell('/bin/sh', sources=['/tmp/source.sh'])
    assert shell.environ('NAME') == 'dockerblade'


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

    expected = 'hello world'
    p = shell.popen(f"echo '{expected}'", encoding=None)
    actual = ''.join([b.decode('utf-8') for b in p.stream]).strip()
    assert actual == expected
