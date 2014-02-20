Next Release
============

*Very soon*

- Added Sphinx docs and ReadTheDocs_ configuration.
- :mod:`tornado.log` is used to log records from :mod:`bonzo.server`.
- Improved test suite to cover the :mod:`bonzo.__init__` and
  :mod:`bonzo.testing` modules.

New modules
~~~~~~~~~~~

- The :mod:`bonzo.mail` module provides a better way to handles messages, this
  module is created to support asynchronous code in the request callback.
- The :mod:`bonzo.errors` module provides custom exceptions for writing error
  codes to the client.

:mod:`bonzo.server`
~~~~~~~~~~~~~~~~~~~

- :class:`~bonzo.server.SMTPConnection` is raising the new exceptions
  from the :mod:`bonzo.errors` module on its ``command_`` methods.
- Added :class:`~bonzo.server.SMTPRequest` for manage the request arguments,
  an instance of this class is passed as argument to the request callback.
- Request callback receives an instance of :class:`~bonzo.server.SMTPRequest`
  now. The message can be found on the :attr:`~bonzo.server.SMTPRequest.message`
  attribute of the request.
- Request callbacks should call to the :meth:`~bonzo.server.SMTPRequest.finish`
  method in order to finish the request by sending a successfully message to the
  client.
- Exceptions in request callbacks no longer silently pass, instead the
  server returns an internal confusion error (``451``) to the client and the
  exceptions are now logged for debugging.

:mod:`bonzo.testing`
~~~~~~~~~~~~~~~~~~~~

- Added ``connect``, ``read_response``, ``send_mail``, and ``close`` methods to
  the :class:`~bonzo.testing.AsyncSMTPTestCase` class. These methods are
  oriented for ease to create tests to the SMTP server.

.. _ReadTheDocs: http://bonzo.readthedocs.org
