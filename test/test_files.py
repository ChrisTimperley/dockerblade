# -*- coding: utf-8 -*-
import pytest

from common import alpine_310


def test_exists(alpine_310):
    files = alpine_310.filesystem()
    assert files.exists('/bin/sh')
    assert files.exists('/bin/cp')
    assert not files.exists('/bin/foobar')


def test_isdir(alpine_310):
    files = alpine_310.filesystem()
    assert not files.isdir('/bin/sh')
    assert files.isdir('/bin')
