# -*- coding: utf-8 -*-
__all__ = ('BackendDriver',)

import abc


class BackendDriver(abc.ABC):
    @abc.abstractmerthod
    def install(self) -> None:
        ...
