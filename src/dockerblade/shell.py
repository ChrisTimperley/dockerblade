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

    def execute(self, command: str) -> Tuple[int, str, float]:
        """Executes a given command and blocks until its completion.

        Returns
        -------
        Tuple[int, str, float]
            The return code, output, and wall-clock running time of the
            execution, measured in seconds.
        """ 
        raise NotImplementedError
