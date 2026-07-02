"""A non-blocking, single-threaded SMTP server."""
import email
import inspect
import socket
import sys

from tornado.escape import to_unicode, utf8
from tornado.ioloop import IOLoop
from tornado.log import app_log, gen_log
from tornado.tcpserver import TCPServer

from bonzo import errors, version

CRLF = '\r\n'


class SMTPServer(TCPServer):
    """A non-blocking, single-threaded SMTP server.

    A server is defined by a request callback that takes an instance of
    :class:`~bonzo.server.SMTPRequest` as an argument.

    A simple example server that handles the request with the received message:

    .. code:: python

        import asyncio
        from bonzo.server import SMTPServer

        async def handle_request(request):
            do_something_with_the_message(request.message)
            await request.finish_async()

        async def main():
            smtp_server = SMTPServer(handle_request)
            smtp_server.listen(2525)
            await asyncio.Event().wait()

        asyncio.run(main())
    """

    def __init__(self, request_callback, **kwargs):
        self.request_callback = request_callback
        TCPServer.__init__(self, **kwargs)

    async def handle_stream(self, stream, address):
        """Handles the stream by executing the request callback."""
        connection = SMTPConnection(stream, address, self.request_callback)
        await connection.run()


class SMTPConnection(object):
    """Handles a connection to an SMTP client, executing SMTP commands.

    This class uses its :attr:`COMMAND` and :attr:`DATA` attributes as a
    simple "enum" to manage the connection state.
    """

    COMMAND = 0
    """Used to set the state to receive any command."""
    DATA = 1
    """Used to set the state to receive data."""

    def __init__(self, stream, address, request_callback):
        self.stream = stream
        self.address = address
        self.request_callback = request_callback
        self.__hostname = None
        self.__data = None
        self._close_callback = None
        self._waiting_for_request = None
        self.reset_arguments()
        if self.stream.socket.family in (socket.AF_INET, socket.AF_INET6):
            self.remote_ip = self.address[0]
        else:
            # Unix (or other) socket; fake the remote address
            self.remote_ip = '0.0.0.0'  # pragma: no cover
        self.stream.set_close_callback(self._on_connection_close)

    async def run(self):
        """Runs the SMTP command loop for this connection."""
        try:
            await self.write('220 Bonzo SMTP Server %s' % version)
            delimiter = CRLF
            while not self.stream.closed():
                line = await self.stream.read_until(utf8(delimiter))
                delimiter = await self._handle_line(line)
        except Exception as e:
            if not self.stream.closed():
                await self._handle_request_exception(e)
        finally:
            self._clear_request_state()

    def reset_arguments(self):
        self.__state = self.COMMAND
        self.__mail = None
        self.__rcpt = []

    def _clear_request_state(self):
        """Clears the per-request state."""
        self.reset_arguments()
        self._close_callback = None
        if (self._waiting_for_request is not None and
                not self._waiting_for_request.done()):
            self._waiting_for_request.set_result(None)
        self._waiting_for_request = None

    def set_close_callback(self, callback):
        """Sets a callback that will be run when the connection is closed."""
        self._close_callback = callback

    def _on_connection_close(self):
        if self._close_callback is not None:
            callback = self._close_callback
            self._close_callback = None
            callback()
        if (self._waiting_for_request is not None and
                not self._waiting_for_request.done()):
            self._waiting_for_request.set_result(None)

    def close(self):
        """Close the stream."""
        self.stream.close()
        self._clear_request_state()

    async def write(self, chunk):
        """Writes a chunk of output to the stream."""
        if not self.stream.closed():
            await self.stream.write(utf8(chunk + CRLF))

    async def write_ok(self, message='Ok'):
        """Writes a successful ``250`` status response."""
        await self.write('%s %s' % (250, message))

    def finish(self):
        """Finishes the request by closing the connection."""
        self.close()

    async def _handle_line(self, line):
        try:
            if self.__state == self.COMMAND:
                line = to_unicode(line)[:-2]  # Remove delimiter '\r\n'
                if not line.strip():
                    raise errors.UnrecognisedCommand()
                i = line.find(' ')
                if i < 0:
                    command = line
                    arg = None
                else:
                    command = line[:i]
                    arg = line[i + 1:].strip()
                method = getattr(self, 'command_' + command.lower(), None)
                if not method:
                    raise errors.NotImplementedCommand(command)
                result = method(arg)
                if inspect.isawaitable(result):
                    result = await result
                return result or CRLF
            elif self.__state == self.DATA:
                line = to_unicode(line)[:-5]  # Remove delimiter '\r\n.\r\n'
                data = []
                for text in line.split(CRLF):
                    if text and text[0] == '.':
                        data.append(text[1:])
                    else:
                        data.append(text)
                await self._on_data('\n'.join(data))
                return CRLF
            else:
                raise errors.InternalConfusion()
        except Exception as e:
            await self._handle_request_exception(e)
            return CRLF

    def _request_summary(self):
        return ''

    def log_exception(self, typ, value, tb):
        if isinstance(value, errors.SMTPError):
            if value.log_message:
                _format = '%d %s' + value.log_message
                args = ([value.status_code, self._request_summary()] +
                        list(value.args))
                gen_log.warning(_format, *args)
        else:
            app_log.error('Uncaught exception %s', self._request_summary(),
                          exc_info=(typ, value, tb))

    async def _handle_request_exception(self, e):
        self.log_exception(*sys.exc_info())
        if not isinstance(e, errors.SMTPError):
            e = errors.InternalConfusion()
        await self.write('%d %s' % (e.status_code, e.message))

    def __getaddr(self, keyword, arg):
        address = None
        keylen = len(keyword)
        if arg[:keylen].upper() == keyword:
            address = arg[keylen:].strip()
            if not address:
                pass
            elif address[0] == '<' and address[-1] == '>' and address != '<>':
                # Addresses can be in the form <person@dom.com> but watch out
                # for null address, e.g. <>
                address = address[1:-1]
        return address

    async def command_helo(self, arg):
        """Handles the ``HELO`` SMTP command."""
        if not arg:
            raise errors.BadArguments('HELO hostname')
        if self.__hostname:
            raise errors.BadSequence('Duplicate HELO/EHLO')
        self.__hostname = arg
        await self.write('250 Hello %s' % self.remote_ip)

    async def command_noop(self, arg):
        """Handles the ``NOOP`` SMTP command."""
        if arg:
            raise errors.BadArguments('NOOP')
        await self.write_ok()

    async def command_quit(self, arg):
        """Handles the ``QUIT`` SMTP command."""
        await self.write('221 Bye')
        self.finish()

    async def command_mail(self, arg):
        """Handles the ``MAIL`` SMTP command."""
        if not self.__hostname:
            raise errors.BadSequence('Error: need HELO command')
        address = self.__getaddr('FROM:', arg) if arg else None
        if not address:
            raise errors.BadArguments('MAIL FROM:<address>')
        if self.__mail:
            raise errors.BadSequence('Error: nested MAIL command')
        self.__mail = address
        await self.write_ok()

    async def command_rcpt(self, arg):
        """Handles the ``RCPT`` SMTP command."""
        if not self.__mail:
            raise errors.BadSequence('Error: need MAIL command')
        address = self.__getaddr('TO:', arg) if arg else None
        if not address:
            raise errors.BadArguments('RCPT TO:<address>')
        self.__rcpt.append(address)
        await self.write_ok()

    async def command_rset(self, arg):
        """Handles the ``RSET`` SMTP command."""
        if arg:
            raise errors.BadArguments('RSET')
        self.reset_arguments()
        await self.write_ok()

    async def command_data(self, arg):
        """Handles the ``DATA`` SMTP command."""
        if not self.__rcpt:
            raise errors.BadSequence('Error: need RCPT command')
        if arg:
            raise errors.BadArguments('DATA')
        self.__state = self.DATA
        await self.write('354 End data with <CR><LF>.<CR><LF>')
        return '{0}.{0}'.format(CRLF)

    async def _on_data(self, data):
        self.__data = data
        request = SMTPRequest(self, self.remote_ip, 'DATA',
                              hostname=self.__hostname, mail=self.__mail,
                              rcpt=self.__rcpt, data=self.__data)
        finish_waiter = self.wait_for_request_finish()
        result = self.request_callback(request)
        if inspect.isawaitable(result):
            await result
        await finish_waiter

    async def request_finished(self):
        self.reset_arguments()
        await self.write_ok()

    def wait_for_request_finish(self):
        if self._waiting_for_request is None or self._waiting_for_request.done():
            loop = IOLoop.current().asyncio_loop
            self._waiting_for_request = loop.create_future()
        return self._waiting_for_request

    def notify_request_finished(self):
        if (self._waiting_for_request is not None and
                not self._waiting_for_request.done()):
            self._waiting_for_request.set_result(None)


class SMTPRequest(object):
    """A single SMTP request.
    """

    def __init__(self, connection, remote_ip, command, hostname=None, mail=None,
                 rcpt=None, data=None):
        self.connection = connection
        self.remote_ip = remote_ip
        self.command = command
        self.hostname = hostname
        self.mail = mail
        self.rcpt = rcpt or []
        self.data = data

    @property
    def message(self):
        """Returns an instance of a subclass from the
        :class:`email.mime.base.MIMEBase` class. It's actually parsed from the
        data received using the :meth:`~email.message_from_string` method.
        """
        if not hasattr(self, '_message'):
            self._message = email.message_from_string(self.data)
        return self._message

    async def finish_async(self):
        """Writes a successful response to the connection."""
        try:
            await self.connection.request_finished()
        finally:
            self.connection.notify_request_finished()

    def finish(self):
        """Writes a successful response to the connection."""
        IOLoop.current().spawn_callback(self.finish_async)

    def __repr__(self):
        attrs = ('remote_ip', 'hostname', 'mail', 'rcpt')
        args = ', '.join(["%s='%s'" % (n, getattr(self, n)) for n in attrs])
        return '%s (%s)' % (self.__class__.__name__, args)
