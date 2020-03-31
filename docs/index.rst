.. -*-restructuredtext-*-

dockerblade
===========

.. image:: https://travis-ci.org/ChrisTimperley/dockerblade.svg?branch=master
    :target: https://travis-ci.org/ChrisTimperley/dockerblade

.. image:: https://badge.fury.io/py/dockerblade.svg
    :target: https://badge.fury.io/py/dockerblade

.. image:: https://img.shields.io/pypi/pyversions/dockerblade.svg
    :target: https://pypi.org/project/dockerblade

.. image:: https://coveralls.io/repos/github/ChrisTimperley/dockerblade/badge.svg
    :target: https://coveralls.io/github/ChrisTimperley/dockerblade

Dockerblade makes it easy to interact with Docker containers by providing an
API,
inspired by Python's standard libraries
(e.g.,
`subprocess <https://docs.python.org/3/library/subprocess.html>`_,
`os <https://docs.python.org/3/library/os.html>`_,
and
`io <https://docs.python.org/3/library/io.html>`_)
for executing commands and interacting with filesystems.


API Documentation
-----------------

.. toctree::
   :maxdepth: 2

   dockerblade.container
   dockerblade.daemon
   dockerblade.exceptions
   dockerblade.files
   dockerblade.popen
   dockerblade.shell
   dockerblade.stopwatch
