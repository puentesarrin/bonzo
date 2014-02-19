# -*- coding: utf-8 -*-
"""Tools for handling requests with asynchronous features."""
import functools

from tornado.concurrent import Future


class MessageHandler(object):
    """Subclass this class and define ``data()`` to make a handler.

    Instances of this class are callable and can be passed directly to
    SMTPServer to handle messages:

    .. code-block:: python

       from tornado import ioloop
       from bonzo import server
       from bonzo.mail import MessageHandler


       class Handler(MessageHandler):

           def data(self, request):
               print(request.message)

       smtp_server = server.SMTPServer(Handler())
       smtp_server.listen(2525)
       ioloop.IOLoop.current().start()
    """

    def __init__(self, **settings):
        self.settings = settings
        if self.settings.get('debug'):
            self.settings.setdefault('autoreload', True)

        # Automatically reload modified modules
        if self.settings.get('autoreload'):
            from tornado import autoreload
            autoreload.start()

    def listen(self, port, address='', **kwargs):
        """Starts an SMTP server for this handler on the given port.

        This is a convenience alias for creating an
        :class:`~bonzo.server.SMTPServer` object and calling its listen method.
        Keyword arguments not supported by :meth:`bonzo.server.SMTPServer.listen
        <tornado.tcpserver.TCPServer.listen>` are passed to the
        :class:`~bonzo.server.SMTPServer` constructor.  For advanced uses
        (e.g. multi-process mode), do not use this method; create an
        :class:`~bonzo.server.SMTPServer` and call its
        :meth:`~tornado.tcpserver.TCPServer.bind`/
        :meth:`~tornado.tcpserver.TCPServer.start` methods directly.

        Note that after calling this method you still need to call
        ``IOLoop.current().start()`` to start the server.
        """
        from bonzo.server import SMTPServer
        server = SMTPServer(self, **kwargs)
        server.listen(port, address)

    def __call__(self, request):
        """Called by :class:`~bonzo.server.SMTPServer` to execute the
        request.
        """
        method = getattr(self, request.command.lower())
        self._when_complete(method(request), request.finish)

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

    def data(self, request):
        pass
