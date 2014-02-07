Next Release
============

*Very soon*

- Added Sphinx docs and ReadTheDocs.
- :mod:`tornado.log` is used to log records from :mod:`bonzo.server`.

New modules
~~~~~~~~~~~

- The :mod:`bonzo.errors` module provides custom exceptions for writing error
  codes to the client.

:mod:`bonzo.server`
~~~~~~~~~~~~~~~~~~~

- :class:`~bonzo.server.SMTPConnection` is raising the new exceptions
  from :mod:`bonzo.errors` module on commands methods.