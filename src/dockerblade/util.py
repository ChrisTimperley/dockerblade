"""Provides a number of utility methods."""
__all__ = ("quote_host", "quote_container")

import functools
import os
import shlex
from collections.abc import Callable

import mslex

quote_host: Callable[[str], str]
quote_container = shlex.quote

if os.name == "nt":
    quote_host = functools.partial(mslex.quote, for_cmd=True)
else:
    quote_host = shlex.quote
