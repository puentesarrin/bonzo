# -*- coding: utf-8 -*-
"""Tools for handling requests with asynchronous features."""
import functools

from tornado.concurrent import Future


class RequestHandler(object):
    """Subclass this class and define :meth:`data()` to make a handler.
    """

    def __init__(self, application, request):
        self.application = application
        self.request = request
        self._finished = False
        self._auto_finish = True

    @property
    def settings(self):
        """An alias for :attr:`self.application.settings
        <Application.settings>`."""
        return self.application.settings

    def data(self):
        pass

    def prepare(self):
        """Called at the beginning of a request before :meth:`data`.

        Override this method to perform common initialization regardless
        of the request method.
        """
        pass

    def on_finish(self):
        """Called after the end of a request.

        Override this method to perform cleanup, logging, etc. This method is a
        counterpart to :meth:`prepare`.  ``on_finish`` may not produce any
        output, as it is called after the response has been sent to the client.
        """
        pass

    def _when_complete(self, result, callback):
        if result is None:
            callback()
        elif isinstance(result, Future):
            if result.done():
                if result.result() is not None:
                    raise ValueError('Expected None, got %r' % result.result())
                callback()
            else:
                from tornado.ioloop import IOLoop
                IOLoop.current().add_future(
                    result, functools.partial(self._when_complete,
                                              callback=callback))
        else:
            raise ValueError("Expected Future or None, got %r" % result)

    def _execute(self):
        """Executes this request."""
        self._when_complete(self.prepare(), self._execute_method)

    def _execute_method(self):
        if not self._finished:
            method = getattr(self, self.request.command.lower())
            self._when_complete(method(), self._execute_finish)

    def _execute_finish(self):
        if self._auto_finish and not self._finished:
            self.finish()

    def finish(self):
        """Finishes this response, ending the SMTP request."""
        if self._finished:
            raise RuntimeError("finish() called twice.")
        self.request.finish()
        self._finished = True
        self.on_finish()


class Application(object):
    """Instances of this class are callable and can be passed directly to
    SMTPServer to handle messages:

    .. code-block:: python

       from tornado import ioloop
       from bonzo import server
       from bonzo.mail import RequestHandler


       class Handler(RequestHandler):

           def data(self):
               print(self.request.message)

       application = mail.Application(Handler)
       smtp_server = server.SMTPServer(application)
       smtp_server.listen(2525)
       ioloop.IOLoop.current().start()

    .. attribute:: settings

         Additional keyword arguments passed to the constructor are saved in
         the ``settings`` dictionary, and are often referred to in
         documentation as "application settings".  Settings are used to
         customize various aspects of Bonzo (although in some cases richer
         customization is possible by overriding methods in a subclass of
         :class:`RequestHandler`). Some applications also like to use the
         ``settings`` dictionary as a way to make application-specific settings
         available to handlers without using global variables.
    """

    def __init__(self, handler_class, **settings):
        self.handler_class = handler_class
        self.settings = settings
        if self.settings.get('debug'):
            self.settings.setdefault('autoreload', True)

        # Automatically reload modified modules
        if self.settings.get('autoreload'):
            from tornado import autoreload
            autoreload.start()

    def __call__(self, request):
        """Called by :class:`~bonzo.server.SMTPServer` to execute the
        request.
        """
        handler = self.handler_class(self, request)
        handler._execute()

    def listen(self, port, address='', **kwargs):
        """Starts an SMTP server for this handler on the given port.

        This is a convenience alias for creating an
        :class:`.SMTPServer` object and calling its listen method.
        Keyword arguments not supported by :meth:`SMTPServer.listen
        <tornado.tcpserver.TCPServer.listen>` are passed to the
        :class:`~.server.SMTPServer` constructor.  For advanced uses
        (e.g. multi-process mode), do not use this method; create an
        :class:`~.server.SMTPServer` and call its
        :meth:`~tornado.tcpserver.TCPServer.bind`/
        :meth:`~tornado.tcpserver.TCPServer.start` methods directly.

        Note that after calling this method you still need to call
        ``IOLoop.current().start()`` to start the server.
        """
        from bonzo.server import SMTPServer
        server = SMTPServer(self, **kwargs)
        server.listen(port, address)
