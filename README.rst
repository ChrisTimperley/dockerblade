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


Installation
------------

To install the latest release of dockerblade via `pipenv <https://pipenv.pypa.io/en/latest/>`_
or :code:`pip`:

.. code:: console

   $ pipenv install dockerblade


Usage
-----

To connect to a Docker daemon on the host machine and attach to a running
container:

.. code:: python

   import dockerblade

   daemon = dockerblade.DockerDaemon()
   container = daemon.attach('name-of-the-container')


To perform filesystem operations on a container:

.. code:: python

   filesystem = container.filesystem()

   # write text to a file
   filesystem.write('/tmp/foo', 'Hello world!')

   # remove a file (inspired by os.remove)
   filesystem.remove('/tmp/foo')

   # see API docs for more operations
   ...


To execute commands inside the container:


.. code:: python

   # specify the shell that should be used (e.g., /bin/sh, /bin/bash, /bin/zsh)
   shell = container.shell('/bin/bash')

   # obtain the value of an environment variable
   val = container.environ('LD_LIBRARY_PATH')

   # create a Popen
   process = shell.popen('sleep 5')
   retcode = process.wait()

   # execute a command
   assert shell.check_output('echo "Hello World"') == 'Hello World'

   # see API docs for more operations
   ...


API Documentation
-----------------

API documentation is available at: https://www.christimperley.co.uk/dockerblade
