# -*- coding: utf-8 -*-
__all__ = ('FileSystem',)

import typing
import shlex

import attr

if typing.TYPE_CHECKING:
    from .shell import Shell
    from .container import Container


@attr.s(slots=True)
class FileSystem:
    """Provides access to a Docker filesystem.

    Attributes
    ----------
    container: Container
        The container to which this filesystem belongs.
    """
    container: 'Container' = attr.ib()
    _shell: 'Shell' = attr.ib(repr=False, eq=False, hash=False)

    def exists(self, path: str) -> bool:
        """Determines whether a file or directory exists at the given path.
        Inspired by :meth:`os.path.exists`.
        """
        cmd = f'test -e {shlex.quote(path)}'
        return self._shell.run(cmd, stdout=False).returncode == 0

    def isfile(self, path: str) -> bool:
        """Determines whether a regular file exists at a given path.
        Inspired by :meth:`os.path.isfile`.
        """
        cmd = f'test -f {shlex.quote(path)}'
        return self._shell.run(cmd, stdout=False).returncode == 0

    def isdir(self, path: str) -> bool:
        """Determines whether a directory exists at a given path.
        Inspired by :meth:`os.path.dir`.
        """
        cmd = f'test -d {shlex.quote(path)}'
        return self._shell.run(cmd, stdout=False).returncode == 0

    def islink(self, path: str) -> bool:
        """Determines whether a symbolic link exists at a given path.
        Inspired by :meth:`os.path.islink`.
        """
        cmd = f'test -h {shlex.quote(path)}'
        return self._shell.run(cmd, stdout=False).returncode == 0
