# -*- coding: utf-8 -*-
import pytest

from common import alpine_310


def test_exists(alpine_310):
    files = alpine_310.filesystem()
    assert files.exists('/bin/sh')
