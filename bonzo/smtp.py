"""Tools for handling requests with asynchronous features."""
import inspect

from tornado.log import app_log


class RequestHandler(object):
    """Subclass this class and define :meth:`data()` to make a handler."""

    def __init__(self, application, request):
        self.application = application
        self.request = request
        self._finished = False
        self._auto_finish = True
        self.request.connection.set_close_callback(self.on_connection_close)

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

    def on_connection_close(self):
        """Called in async handlers if the client closed the connection."""
        pass

    async def _when_complete(self, result):
        if inspect.isawaitable(result):
            result = await result
        if result is not None:
            raise ValueError('Expected None, got %r' % result)

    async def _execute(self):
        """Executes this request."""
        await self._when_complete(self.prepare())
        if not self._finished:
            method = getattr(self, self.request.command.lower())
            try:
                await self._when_complete(method())
            except Exception:
                if self._finished:
                    app_log.error('Uncaught exception', exc_info=True)
                else:
                    raise
        if self._auto_finish and not self._finished:
            await self.finish_async()

    async def finish_async(self):
        """Finishes this response, ending the SMTP request."""
        if self._finished:
            raise RuntimeError("finish() called twice.")
        self.request.connection.set_close_callback(None)
        await self.request.finish_async()
        self._finished = True
        self.on_finish()

    def finish(self):
        """Finishes this response, ending the SMTP request."""
        if self._finished:
            raise RuntimeError("finish() called twice.")
        self.request.connection.set_close_callback(None)
        self.request.finish()
        self._finished = True
        self.on_finish()


class Application(object):
    """Instances of this class are callable and can be passed directly to
    SMTPServer to handle messages:

    .. code-block:: python

       async def main():
           application = smtp.Application(Handler)
           smtp_server = server.SMTPServer(application)
           smtp_server.listen(2525)
           await asyncio.Event().wait()

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

    async def __call__(self, request):
        """Called by :class:`~bonzo.server.SMTPServer` to execute the
        request.
        """
        handler = self.handler_class(self, request)
        await handler._execute()

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

        Note that after calling this method you still need to run the active
        asyncio event loop to start the server.
        """
        from bonzo.server import SMTPServer
        server = SMTPServer(self, **kwargs)
        server.listen(port, address)
