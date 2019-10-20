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
