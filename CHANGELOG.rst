v0.5.6 (2020-11-23)
-------------------

* fixed issue when copying symbolically linked files (#73)
* updated Daemon constructor to support Windows out of the box
* fixed `copy_from_host` and `copy_to_host` in `FileSystem` to support
  Windows hosts.
* relaxed dependency versions to improve compatibility.


v0.5.5 (2020-07-08)
-------------------

* updated default `url` for `DockerDaemon` to be the value of the
  `DOCKER_HOST` environment variable, if present. If the `DOCKER_HOST`
  environment variable is not present, `unix://var/run/docker.sock`
  will be used instead.


v0.5.4 (2020-06-29)
-------------------

* added `command` parameter to `provision` method of `DockerDaemon`.


v0.5.3 (2020-06-29)
-------------------

* added `name` attribute to `Container` class.
* added `ports`, `user`, `name`, `environment`, and `entrypoint` parameters to
  `provision` method of `DockerDaemon`.
* bug fix: added `py.typed` to `MANIFEST.in` to fix PEP 561 support.
* added `__enter__` and `__exit__` to `Container`.


v0.5.2 (2020-06-09)
-------------------

* improved performance of `copy_to_host`, `copy_from_host`, and `read` methods
  in `FileSystem`.
* added `network_mode` parameter to `provision` method of `DockerDaemon`.
* added `network_mode` property to `Container`.


v0.5.1 (2020-06-01)
-------------------

* bug fix: lack of defensive copying in Shell constructor can lead to
  crashes due to use of mappingproxy type.


v0.5.0 (2020-05-29)
-------------------

* added experimental `_local_to_host_pid` method to Shell API.


v0.4.2 (2020-05-29)
-------------------

* added support for mypy type hint discovery as specified in PEP 561
* added missing type annotations


v0.4.1 (2020-04-23)
-------------------

* updated :code:`Shell` construction to raise a :code:`ContainerFileNotFound`
  if a given source does not exist.
* added :code:`access` method to `FileSystem` for testing whether user inside
  shell has permission to perform operations on a given file.


v0.4.0 (2020-04-10)
-------------------

* updated :code:`TimeoutExpired` and :code:`CalledProcessError` exceptions to
  inherit from their counterparts in the Python standard library
* added :code:`encoding` parameter to :code:`Popen` to allow users to specify
  which encoding, if any, should be used to decode the output stream from a
  process.
* added :code:`volumes` parameter to :code:`provision` method in
  :code:`DockerDaemon`, allowing users to specify volume mounts.


v0.3.0 (2020-03-13)
-------------------

* added `persist` method to `Container`
* added `pid` property `Container`
* added `_info` property to `Container`
* added `find` method to `FileSystem`
* added `listdir` method to `FileSystem`
* added `mkdir` method to `FileSystem`
* added `rmdir` method to `FileSystem`
* added ability to specify an environment via `environment` argument of
  `shell` method in `Container`
* added ability to construct a shell using sources via `sources` argument
  of `shell` method in `Container`
* optimised implementation of `environ` method in `Shell` by removing the
  need to interact with the underlying container


v0.2.3 (2020-01-22)
-------------------

* added ip_address property to Container


v0.2.2 (2020-01-13)
-------------------

* disabled stdout logging by default


v0.2.1 (2019-12-30)
-------------------

* added time_limit and kill_after to command execution methods in Shell
* added makedirs to FileSystem
* added mktemp to FileSystem
* added remove to FileSystem
* added write to FileSystem
* added tempfile method to FileSystem
* fixed bug in copy_from_host that prevented files from being copied to the
  container
* implemented provision method in Daemon


v0.2.0 (2019-12-17)
-------------------

* added copy_from_host method to FileSystem


v0.1.0 (2019-12-16)
-------------------

* added read method to FileSystem
* added copy_to_host method to FileSystem


v0.0.2 (2019-12-16)
-------------------

* updated attrs to 19.3.0


v0.0.1 (2019-10-12)
-------------------

* initial release.
