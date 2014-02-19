# -*- coding: utf-8 -*-
"""A non-blocking, single-threaded SMTP server."""
import email
import functools
import socket
import sys

from tornado.escape import to_unicode, utf8
from tornado.log import app_log, gen_log
from tornado.tcpserver import TCPServer
from tornado import stack_context

from bonzo import errors, version

CRLF = '\r\n'


class SMTPServer(TCPServer):
    """A non-blocking, single-threaded SMTP server.

    A server is defined by a request callback that takes an instance of
    :class:`~bonzo.server.SMTPRequest` as an argument.

    A simple example server that handles the request with the received message:

    .. code:: python

        from tornado.ioloop import IOLoop
        from bonzo.server import SMTPServer

        def handle_request(request):
            do_something_with_the_message(request.message)
            request.finish()

        smtp_server = SMTPServer(handle_request)
        smtp_server.listen()
        IOLoop.current().start()
    """

    def __init__(self, request_callback, io_loop=None, **kwargs):
        self.request_callback = request_callback
        TCPServer.__init__(self, io_loop=io_loop, **kwargs)

    def handle_stream(self, stream, address):
        """Handles the stream by executing the request callback.
        """
        SMTPConnection(stream, address, self.request_callback)


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
        self.reset_arguments()
        if self.stream.socket.family in (socket.AF_INET, socket.AF_INET6):
            self.remote_ip = self.address[0]
        else:
            # Unix (or other) socket; fake the remote address
            self.remote_ip = '0.0.0.0'  # pragma: no cover
        self._clear_request_state()
        self._command_callback = stack_context.wrap(self._on_commands)
        self.stream.set_close_callback(self._on_connection_close)
        self.write('220 Bonzo SMTP Server %s' % version)

    def reset_arguments(self):
        self.__state = self.COMMAND
        self.__mail = None
        self.__rcpt = []

    def _clear_request_state(self):
        """Clears the per-request state.

        This is run in between requests to allow the previous handler
        to be garbage collected (and prevent spurious close callbacks),
        and when the connection is closed (to break up cycles and
        facilitate garbage collection in cpython).
        """
        self.reset_arguments()
        self._request_finished = False
        self._write_callback = None
        self._close_callback = None

    def set_close_callback(self, callback):
        """Sets a callback that will be run when the connection is closed.
        """
        self._close_callback = stack_context.wrap(callback)

    def _on_connection_close(self):
        if self._close_callback is not None:
            callback = self._close_callback
            self._close_callback = None
            callback()
        # Delete any unfinished callbacks to break up reference cycles.
        self._clear_request_state()

    def close(self):
        """Close the stream.
        """
        self.stream.close()
        # Remove this reference to self, which would otherwise cause a
        # cycle and delay garbage collection of this connection.
        self._clear_request_state()

    def write(self, chunk, callback=None, read_until_delimiter=CRLF):
        """Writes a chunk of output to the stream."""
        if not self.stream.closed():
            if callback is None:
                callback = functools.partial(self.stream.read_until,
                                             utf8(read_until_delimiter),
                                             self._on_commands)
            self._write_callback = stack_context.wrap(callback)
            self.stream.write(utf8(chunk + CRLF), self._on_write_complete)

    def write_ok(self, message='Ok', callback=None, read_until_delimiter=CRLF):
        """Writes a successfully message to the output by sending a ``250``
        status code.
        """
        self.write('%s %s' % (250, message), callback=callback,
                   read_until_delimiter=read_until_delimiter)

    def finish(self):
        """Finishes the request."""
        if not self.stream.writing():
            self.stream.close()

    def _on_write_complete(self):
        if self._write_callback is not None:
            callback = self._write_callback
            self._write_callback = None
            callback()
        # _on_write_complete is enqueued on the IOLoop whenever the
        # IOStream's write buffer becomes empty, but it's possible for
        # another callback that runs on the IOLoop before it to
        # simultaneously write more data and finish the request.  If
        # there is still data in the IOStream, a future
        # _on_write_complete will be responsible for calling
        # _finish_request.
        if self._request_finished and not self.stream.writing():
            self._finish_request()

    def _finish_request(self):
        self.close()

    def _on_commands(self, line):
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
                method(arg)
            elif self.__state == self.DATA:
                line = to_unicode(line)[:-5]  # Remove delimiter '\r\n.\r\n'
                data = []
                for text in line.split(CRLF):
                    if text and text[0] == '.':
                        data.append(text[1:])
                    else:
                        data.append(text)
                self._on_data('\n'.join(data))
            else:
                raise errors.InternalConfusion()
        except Exception as e:
            self._handle_request_exception(e)

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

    def _handle_request_exception(self, e):
        self.log_exception(*sys.exc_info())
        if not isinstance(e, errors.SMTPError):
            e = errors.InternalConfusion()
        self.write('%d %s' % (e.status_code, e.message))

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

    def command_helo(self, arg):
        """Handles the ``HELO`` SMTP command.

        - Raises a :class:`~bonzo.errors.BadArguments` error code when the
          network name of the connecting machine is not received.
        - Raises a :class:`~bonzo.errors.BadSequence` when a ``HELO`` command
          already was received.
        """
        if not arg:
            raise errors.BadArguments('HELO hostname')
        if self.__hostname:
            raise errors.BadSequence('Duplicate HELO/EHLO')
        self.__hostname = arg
        self.write('250 Hello %s' % self.remote_ip)

    def command_noop(self, arg):
        """Handles the ``NOOP`` SMTP command.

        - Raises a :class:`~bonzo.errors.BadArguments` when an argument is not
          received.
        """
        if arg:
            raise errors.BadArguments('NOOP')
        self.write_ok()

    def command_quit(self, arg):
        """Handles the ``QUIT`` SMTP command.
        """
        self.write('221 Bye', self.finish)

    def command_mail(self, arg):
        """Handles the ``MAIL`` SMTP command.

        - Raises a :class:`~bonzo.errors.BadArguments` when the ``from`` address
          is not received.
        - Raises a :class:`~bonzo.errors.BadSequence` when a ``MAIL`` command
          already was received.
        """
        address = self.__getaddr('FROM:', arg) if arg else None
        if not address:
            raise errors.BadArguments('MAIL FROM:<address>')
        if self.__mail:
            raise errors.BadSequence('Error: nested MAIL command')
        self.__mail = address
        self.write_ok()

    def command_rcpt(self, arg):
        """Handles the ``RCPT`` SMTP command.

        - Raises a :class:`~bonzo.errors.BadSequence` when a ``MAIL`` command
          was not previously received.
        - Raises a :class:`~bonzo.errors.BadArguments` when the ``to`` address
          is not received.
        """
        if not self.__mail:
            raise errors.BadSequence('Error: need MAIL command')
        address = self.__getaddr('TO:', arg) if arg else None
        if not address:
            raise errors.BadArguments('RCPT TO:<address>')
        self.__rcpt.append(address)
        self.write_ok()

    def command_rset(self, arg):
        """Handles the ``RSET`` SMTP command.

        - Raises a :class:`~bonzo.errors.BadArguments` when an argument is not
          received.
        """
        if arg:
            raise errors.BadArguments('RSET')
        self.reset_arguments()
        self.write_ok()

    def command_data(self, arg):
        """Handles the ``DATA`` SMTP command.

        - Raises a :class:`~bonzo.errors.BadSequence` when a ``RCPT`` command
          was not previously received.
        - Raises a :class:`~bonzo.errors.BadArguments` when an argument is not
          received.
        """
        if not self.__rcpt:
            raise errors.BadSequence('Error: need RCPT command')
        if arg:
            raise errors.BadArguments('DATA')
        self.__state = self.DATA
        self.write('354 End data with <CR><LF>.<CR><LF>',
                   read_until_delimiter='{0}.{0}'.format(CRLF))

    def _on_data(self, data):
        self.__data = data
        request = SMTPRequest(self, self.remote_ip, 'DATA',
                              hostname=self.__hostname, mail=self.__mail,
                              rcpt=self.__rcpt, data=self.__data)
        self.request_callback(request)


class SMTPRequest(object):
    """A single SMTP request.
    """

    def __init__(self, connection, remote_ip, command, hostname=None, mail=None,
                 rcpt=[], data=None):
        self.connection = connection
        self.remote_ip = remote_ip
        self.command = command
        self.hostname = hostname
        self.mail = mail
        self.rcpt = rcpt
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

    def finish(self):
        """Writes to the connection a successfully message."""
        self.connection.reset_arguments()
        self.connection.write_ok()

    def __repr__(self):
        attrs = ('remote_ip', 'hostname', 'mail', 'rcpt')
        args = ', '.join(["%s=%r" % (n, getattr(self, n)) for n in attrs])
        return '%s (%s)' % (self.__class__.__name__, args)
