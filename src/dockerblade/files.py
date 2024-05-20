__all__ = ("FileSystem",)

import contextlib
import os
import subprocess
import tempfile
import typing
from collections.abc import Iterator
from pathlib import Path
from typing import Literal, overload

import attr
from loguru import logger

from . import exceptions as exc
from .util import quote_container, quote_host

if typing.TYPE_CHECKING:
    from .container import Container
    from .shell import Shell

_ON_WINDOWS = os.name == "nt"

EXIT_CODE_FILE_NOT_FOUND = 50
EXIT_CODE_IS_NOT_A_DIRECTORY = 51
EXIT_CODE_FILE_ALREADY_EXISTS = 49


@attr.s(slots=True)
class FileSystem:
    """Provides access to a Docker filesystem.

    Attributes
    ----------
    container: Container
        The container to which this filesystem belongs.
    """
    container: "Container" = attr.ib()
    _shell: "Shell" = attr.ib(repr=False, eq=False, hash=False)

    def copy_from_host(self, path_host: str, path_container: str) -> None:
        """Copies a given file or directory tree from the host to the container.

        Parameters
        ----------
        path_host: str
            the file or directory tree that should be copied from the host.
        path_container: str
            the destination path on the container.

        Raises
        ------
        ContainerFileNotFound
            if no file or directory exists at the given path inside the
            container.
        HostFileNotFound
            if the parent directory of the host filepath does not exist.
        CopyFailed
            if the copy operation failed.
        """
        id_container: str = self.container.id
        if not os.path.exists(path_host):
            raise exc.HostFileNotFound(path_host)

        path_host_escaped = quote_host(path_host)
        path_container_escaped = quote_host(path_container)

        if _ON_WINDOWS:
            if path_container_escaped[0] != '"':
                path_container_escaped = f'"{path_container_escaped}"'
            if path_host_escaped[0] != '"':
                path_host_escaped = f'"{path_host_escaped}"'

        cmd: str = (f"docker cp -L {path_host_escaped} "
                    f"{id_container}:{path_container_escaped}")
        try:
            subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError as error:
            path_container_parent: str = os.path.dirname(path_container)
            if not self.isdir(path_container_parent):
                raise exc.ContainerFileNotFound(
                    path=path_container_parent,
                    container_id=id_container,
                ) from error

            reason = (f"failed to copy file [{path_host}] "
                      f"from host to container [{id_container}]: "
                      f"{path_container}")
            raise exc.CopyFailed(reason) from error

    def copy_to_host(self,
                     path_container: str,
                     path_host: str,
                     ) -> None:
        """Copies a given file or directory tree from the container to the host.

        Parameters
        ----------
        path_container: str
            the file that should be copied from the container.
        path_host: str
            the destination filepath on the host.

        Raises
        ------
        ContainerFileNotFound
            if no file or directory exists at the given path inside the
            container.
        HostFileNotFound
            if the parent directory of the host filepath does not exist.
        CopyFailed
            if the copy operation failed.
        """
        id_container: str = self.container.id
        path_host_parent: str = os.path.dirname(path_host)
        if not os.path.isdir(path_host_parent):
            raise exc.HostFileNotFound(path_host_parent)

        path_host_escaped = quote_host(path_host)
        path_container_escaped = quote_host(path_container)

        if _ON_WINDOWS:
            if path_container_escaped[0] != '"':
                path_container_escaped = f'"{path_container_escaped}"'
            if path_host_escaped[0] != '"':
                path_host_escaped = f'"{path_host_escaped}"'

        cmd: str = (f"docker cp -L "
                    f"{id_container}:{path_container_escaped} "
                    f"{path_host_escaped}")
        try:
            subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError as error:
            if not self.exists(path_container):
                raise exc.ContainerFileNotFound(
                    path=path_container,
                    container_id=id_container,
                ) from error

            reason = (f"failed to copy file [{path_container}] "
                      f"from container [{id_container}] to host: "
                      f"{path_host}")
            raise exc.CopyFailed(reason) from error

    def remove(self, filename: str) -> None:
        """Removes a given file.

        Inspired by :meth:`os.remove`.

        Warning:
        -------
        Does not handle permissions errors.

        Raises:
        ------
        ContainerFileNotFound
            if the given file does not exist.
        IsADirectoryError
            if the given path is a directory.
        UnexpectedError
            if an unexpected failure occurs.
        """
        command = f"rm {quote_container(filename)}"
        try:
            self._shell.check_call(command)
        except exc.CalledProcessError as error:
            if not self.exists(filename):
                raise exc.ContainerFileNotFound(
                    path=filename,
                    container_id=self.container.id,
                ) from error

            if self.isdir(filename):
                raise exc.IsADirectoryError(
                    path=filename,
                ) from error

            error_message = "failed to remove file"
            raise exc.UnexpectedError(
                error_message,
                error,
            ) from error

    def rmdir(self, directory: str) -> None:
        """Removes a given directory.

        Inspired by :meth:`os.rmdir`.

        Warning:
        -------
        Does not handle permissions errors.

        Raises:
        ------
        ContainerFileNotFound
            if the given directory does not exist.
        IsNotADirectoryError
            if the given path is not a directory.
        OSError
            if the given directory is not empty.
        UnexpectedError
            an unexpected failure occurred.
        """
        escaped_directory = quote_container(directory)
        command = (f"test -e {escaped_directory} || exit 50 && "
                   f"test -d {escaped_directory} || exit 51 && "
                   f"rmdir {escaped_directory}")
        try:
            self._shell.check_output(command, text=True)
        except exc.CalledProcessError as error:
            if error.returncode == EXIT_CODE_FILE_NOT_FOUND:
                raise exc.ContainerFileNotFound(
                    path=directory,
                    container_id=self.container.id,
                ) from error
            if error.returncode == EXIT_CODE_IS_NOT_A_DIRECTORY:
                raise exc.IsNotADirectoryError(
                    path=directory,
                ) from error
            if error.output and "Directory not empty" in error.output:
                raise exc.DirectoryNotEmpty(
                    path=directory,
                ) from error
            raise exc.UnexpectedError('failed to remove directory', error) from error  # noqa

    def write(self, filename: str, contents: str | bytes) -> None:
        """Writes to a given file.

        Parameters
        ----------
        filename: str
            absolute path to the file.
        contents: Union[str, bytes]
            the text or binary contents of the file.
        """
        mode = "wb" if isinstance(contents, bytes) else "w"
        directory = os.path.dirname(filename)
        if not self.isdir(directory):
            raise exc.ContainerFileNotFound(path=directory,
                                            container_id=self.container.id)

        # write to a temporary file on the host and copy to container
        with tempfile.TemporaryDirectory() as host_temp_dir:
            temp_filename = os.path.join(host_temp_dir, "contents")
            with open(temp_filename, mode) as fh:
                fh.write(contents)
            self.copy_from_host(temp_filename, filename)

    @overload
    def read(self, filename: str) -> str:
        ...

    @overload
    def read(self, filename: str, binary: Literal[True]) -> bytes:
        ...

    @overload
    def read(self, filename: str, binary: Literal[False]) -> str:
        ...

    def read(self, filename: str, binary: bool = False) -> str | bytes:
        """Reads the contents of a given file.

        Parameters
        ----------
        filename: str
            absolute path to the file.
        binary: bool
            if :code:`True`, read the binary contents of the file; otherwise,
            treat the file as a text file.

        Raises
        ------
        ContainerFileNotFound
            If no file exists at the given path.
        IsADirectoryError
            If :code:`filename` is a directory.
        """
        mode = "rb" if binary else "r"
        if self.isdir(filename):
            raise exc.IsADirectoryError(filename)

        with tempfile.TemporaryDirectory() as host_temp_dir:
            filename_host_temp = os.path.join(host_temp_dir, "contents")
            self.copy_to_host(filename, filename_host_temp)
            with open(filename_host_temp, mode) as f:
                content: str | bytes = f.read()
                return content

    def find(self, path: str, filename: str) -> list[str]:
        """Returns a list of files that match a filename in a directory, recursively.

        Parameters
        ----------
        path: str
            absolute path to the directory.
        filename: str
            the name of the file to match.

        Returns
        -------
        List[str]
            A list of matching files, given by their absolute paths.

        Raises
        ------
        ContainerFileNotFound
            If the given path belongs to a file.
        IsNotADirectoryError
            If the given path is not a directory.
        UnexpectedError
            If an unexpected error occurred during the find operation.
        """
        # TODO execute as root
        path_escaped = quote_container(path)
        command = (
            f"test ! -e {path_escaped} && exit {EXIT_CODE_FILE_NOT_FOUND} || "
            f"test ! -d {path_escaped} && exit {EXIT_CODE_IS_NOT_A_DIRECTORY} || "
            f"find {path_escaped} -name {quote_container(filename)}"
        )
        try:
            output = self._shell.check_output(command, text=True)
        except exc.CalledProcessError as error:
            if error.returncode == EXIT_CODE_FILE_NOT_FOUND:
                raise exc.ContainerFileNotFound(
                    path=path,
                    container_id=self.container.id,
                ) from error
            if error.returncode == EXIT_CODE_IS_NOT_A_DIRECTORY:
                raise exc.IsNotADirectoryError(
                    path=path,
                ) from error

            error_message = "find failed"
            raise exc.UnexpectedError(
                error_message,
                error=error,
            ) from error

        paths: list[str] = output.replace("\r", "").split("\n")
        return paths

    def makedirs(self, d: str, *, exist_ok: bool = False) -> None:
        """Recursively creates a directory at a given path, creating any missing intermediate directories along the way.

        Inspired by :meth:`os.makedirs`.

        Parameters
        ----------
        d: str
            the path to the directory.
        exist_ok: bool
            specifies whether or not an exception should be raised if the
            given directory already exists.

        Raises
        ------
        ContainerFileAlreadyExists
            if either (a) `exist_ok=False` and a directory already exists at
            the given path, or (b) a file already exists at the given path.
        IsNotADirectoryError
            if the parent directory isn't a directory.
        """
        d_parent = os.path.dirname(d)
        if self.isdir(d) and not exist_ok:
            raise exc.ContainerFileAlreadyExists(path=d,
                                                 container_id=self.container.id)
        if self.isfile(d):
            raise exc.ContainerFileAlreadyExists(path=d,
                                                 container_id=self.container.id)
        if self.exists(d_parent) and self.isfile(d_parent):
            raise exc.IsNotADirectoryError(d_parent)

        command = f"mkdir -p {quote_container(d)}"
        self._shell.check_call(command)

    def exists(self, path: str) -> bool:
        """Determines whether a file or directory exists at the given path.

        Inspired by :meth:`os.path.exists`.
        """
        cmd = f"test -e {quote_container(path)}"
        return self._shell.run(cmd, stdout=False).returncode == 0

    def mkdir(self, directory: str) -> None:
        """Creates a directory at a given path.

        Inspired by :meth:`os.mkdir`.

        Raises
        ------
        IsNotADirectoryError
            if the parent directory isn't a directory.
        ContainerFileNotFound
            if the parent directory doesn't exist.
        ContainerFileAlreadyExists
            if a file or directory already exist at the given path.
        UnexpectedError
            if an unexpected error occurred.
        """
        directory_escaped = quote_container(directory)
        directory_parent = os.path.dirname(directory)
        directory_parent_escaped = quote_container(directory_parent)
        command = (
            f"test -e {directory_escaped} && exit {EXIT_CODE_FILE_ALREADY_EXISTS} || "
            f"test ! -e {directory_parent_escaped} && exit {EXIT_CODE_FILE_NOT_FOUND} || "
            f"test ! -d {directory_parent_escaped} && exit {EXIT_CODE_IS_NOT_A_DIRECTORY} || "
            f"mkdir {directory_escaped}"
        )

        try:
            self._shell.check_call(command)
        except exc.CalledProcessError as error:
            if error.returncode == EXIT_CODE_FILE_ALREADY_EXISTS:
                raise exc.ContainerFileAlreadyExists(
                    path=directory,
                    container_id=self.container.id) from error
            if error.returncode == EXIT_CODE_FILE_NOT_FOUND:
                raise exc.ContainerFileNotFound(
                    path=directory_parent,
                    container_id=self.container.id) from error
            if error.returncode == EXIT_CODE_IS_NOT_A_DIRECTORY:
                raise exc.IsNotADirectoryError(directory_parent) from error

            error_message = "mkdir failed"
            raise exc.UnexpectedError(
                error_message,
                error,
            ) from error

    def listdir(self,
                directory: str,
                *,
                absolute: bool = False,
                ) -> list[str]:
        """Returns a list of the files belonging to a given directory.

        Inspired by :meth:`os.listdir`.

        Parameters
        ----------
        directory: str
            absolute path to the directory.
        absolute: bool
            if :code:`True`, returns a list of absolute paths;
            if :code:`False`, returns a list of relative paths.

        Raises
        ------
        exceptions.IsNotADirectoryError
            if the given path isn't a directory.
        exceptions.ContainerFileNotFound
            if the given path is not a file or directory.
        exceptions.CalledProcessError
            if an unexpected error occurred during execution of this command
        """
        directory_escaped = quote_container(directory)
        command = (
            f"test -e {directory_escaped} || exit {EXIT_CODE_FILE_NOT_FOUND} && "
            f"test -d {directory_escaped} || exit {EXIT_CODE_IS_NOT_A_DIRECTORY} && "
            f"ls --color=never -A -1 {directory_escaped}"
        )
        try:
            output = self._shell.check_output(command, text=True)
        except exc.CalledProcessError as error:
            if error.returncode == EXIT_CODE_FILE_NOT_FOUND:
                raise exc.ContainerFileNotFound(
                    path=directory,
                    container_id=self.container.id,
                ) from error
            if error.returncode == EXIT_CODE_IS_NOT_A_DIRECTORY:
                raise exc.IsNotADirectoryError(
                    path=directory,
                ) from error
            raise

        paths: list[str] = output.replace("\r", "").split("\n")
        if absolute:
            paths = [os.path.join(directory, path) for path in paths]
        return paths

    def isfile(self, path: str) -> bool:
        """Determines whether a regular file exists at a given path.

        Inspired by :meth:`os.path.isfile`.
        """
        cmd = f"test -f {quote_container(path)}"
        return self._shell.run(cmd, stdout=False).returncode == 0

    def isdir(self, path: str) -> bool:
        """Determines whether a directory exists at a given path.

        Inspired by :meth:`os.path.dir`.
        """
        cmd = f"test -d {quote_container(path)}"
        return self._shell.run(cmd, stdout=False).returncode == 0

    def islink(self, path: str) -> bool:
        """Determines whether a symbolic link exists at a given path.

        Inspired by :meth:`os.path.islink`.
        """
        cmd = f"test -h {quote_container(path)}"
        return self._shell.run(cmd, stdout=False).returncode == 0

    def access(self, path: str, mode: int) -> bool:
        """Determines whether the shell user can perform an operation (e.g., existence, read, write, execute).

        Parameters
        ----------
        path: str
            The file or directory that should be checked for access.
        mode:
            The mode that should be checked. Must be either :code:`F_OK`
            or the inclusive OR of one or more of :code:`os.R_OK`,
            :code:`os.W_OK`, and :code:`os.X_OK`.

        Returns
        -------
        :code:`True` if access is allowed, :code:`False` if not.

        Reference
        ---------
        https://docs.python.org/3/library/os.html#os.access
        """
        escaped_path = quote_container(path)

        # check for existence of path
        if mode == os.F_OK:
            return self.exists(path)

        commands: list[str] = []
        if mode & os.X_OK > 0:
            commands.append(f"test -x {escaped_path}")
        if mode & os.R_OK > 0:
            commands.append(f"test -r {escaped_path}")
        if mode & os.W_OK > 0:
            commands.append(f"test -w {escaped_path}")

        if not any(commands):
            return False

        command = " && ".join(commands)
        outcome = self._shell.run(command, stdout=False, stderr=False)
        return outcome.returncode == 0

    def patch(self, context: str, diff: str) -> None:
        """Attempts to atomically apply a given patch to the filesystem.

        Note that this operation is atomic: That is, the patch will either
        be applied in its entirety and the method will return :code:`None`,
        or no changes will be applied to the filesystem and an exception
        will be thrown.

        Parameters
        ----------
        context: str
            The file or directory to which the patch should be applied.
        diff: str
            The contents of patch, given in a unified diff format.

        Raises
        ------
        ValueError
            If the given context is not an absolute path.
        CalledProcessError
            If an error occurred during the application of the patch.
        ContainerFileNotFoundError
            If the given context is neither a file or directory.
        """
        context_path = Path(context)
        if not context_path.is_absolute():
            error = f"context must be supplied as an absolute path: {context}"
            raise ValueError(error)

        with self.tempfile(suffix=".diff") as fn_diff:
            self.write(fn_diff, diff)

            safe_context = quote_container(context)
            safe_fn_diff = quote_container(fn_diff)
            if self.isdir(context):
                cmd = f"patch -u -p0 -f -i {safe_fn_diff} -d {safe_context}"
            elif self.isfile(context):
                cmd = f"patch -u -f -i {safe_fn_diff} {safe_context}"
            else:
                raise exc.ContainerFileNotFound(path=context,
                                                container_id=self.container.id)

            self._shell.check_call(cmd)

    def mktemp(self,
               suffix: str | None = None,
               prefix: str | None = None,
               dirname: str | None = None,
               ) -> str:
        """Creates a temporary file.

        Inspired by :class:`tempfile.mktemp`.

        Parameters
        ----------
        suffix: str, optional
            an optional suffix for the filename.
        prefix: str, optional
            an optional prefix for the filename.
        dirname: str, optional
            if specified, the temporary file will be created in the given
            directory.

        Raises
        ------
        ContainerFileNotFound:
            if specified directory does not exist.

        Returns
        -------
        str
            The absolute path of the temporary file.
        """
        template = quote_container(f"{prefix if prefix else 'tmp'}.XXXXXXXXXX")
        dirname = dirname if dirname else "/tmp"
        cmd_parts = ("mktemp", template, "-p", quote_container(dirname))
        if not self.isdir(dirname):
            raise exc.ContainerFileNotFound(path=dirname,
                                            container_id=self.container.id)
        command = " ".join(cmd_parts)
        filename = self._shell.check_output(command, text=True)

        if suffix:
            original_filename = filename
            filename = original_filename + suffix
            command = f"mv {original_filename} {filename}"
            self._shell.check_call(command)

        return filename

    @contextlib.contextmanager
    def tempfile(self,
                 suffix: str | None = None,
                 prefix: str | None = None,
                 dirname: str | None = None,
                 ) -> Iterator[str]:
        """Creates a temporary file within a context.

        Upon exiting the context, the temporary file will be destroyed.
        Inspired by :class:`tempfile.TemporaryFile`.

        Note:
        ----
        Accepts the same arguments as :meth:`mktemp`.

        Yields:
        ------
        str
            The absolute path of the temporary file.
        """
        filename = self.mktemp(suffix=suffix, prefix=prefix, dirname=dirname)
        yield filename
        try:
            self.remove(filename)
        except exc.ContainerFileNotFound:
            logger.debug("temporary file already destroyed: %s", filename)
