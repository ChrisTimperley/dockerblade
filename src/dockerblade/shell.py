# -*- coding: utf-8 -*-
__all__ = ('Shell',)


class Shell:
    """Provides shell access to a Docker container."""

    def environ(self, var: str) -> str:
        """Reads the value of a given environment variable inside this shell.

        Raises
        ------
        EnvNotFoundError
            if no environment variable exists with the given name.
        """
        raise NotImplementedError
