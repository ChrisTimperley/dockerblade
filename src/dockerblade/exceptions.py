# -*- coding: utf-8 -*-
import attr as _attr


class DockerBladeException:
    """Used by all exceptions that are thrown by DockerBlade."""


@_attr.s(frozen=True, auto_exc=True, auto_attribs=True, str=True)
class EnvNotFoundError(DockerBladeException):
    """No environment variable was found with the given name."""
    name: str

    def __str__(self) -> str:
        return f"No environment variable found with name: {self.name}"
