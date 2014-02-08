Next Release
============

*Very soon*

- Added Sphinx docs and ReadTheDocs_ configuration.
- :mod:`tornado.log` is used to log records from :mod:`bonzo.server`.
- Improved test suite to cover the :mod:`bonzo.__init__` and
  :mod:`bonzo.testing` modules.

New modules
~~~~~~~~~~~

- The :mod:`bonzo.errors` module provides custom exceptions for writing error
  codes to the client.

:mod:`bonzo.server`
~~~~~~~~~~~~~~~~~~~

- :class:`~bonzo.server.SMTPConnection` is raising the new exceptions
  from the :mod:`bonzo.errors` module on its ``command_`` methods.

.. _ReadTheDocs: http://bonzo.readthedocs.org