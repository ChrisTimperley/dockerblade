# -*- coding: utf-8 -*-
import pytest

import dockerblade

from common import alpine_310


def test_run(alpine_310):
    shell = alpine_310.shell('/bin/sh')
    result = shell.run("echo 'hello world'")
    assert result.returncode == 0
    assert result.output == 'hello world'

    # see issue #25
    result = shell.run("echo 'hello world'", stderr=False, stdout=False)
    assert result.returncode == 0
    assert result.output == None


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
