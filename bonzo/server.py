# -*- coding: utf-8 -*-
"""A non-blocking, single-threaded SMTP server."""
import email
import functools

from tornado.escape import to_unicode, utf8
from tornado.tcpserver import TCPServer
from tornado import stack_context

from bonzo import version

CRLF = '\r\n'


class SMTPServer(TCPServer):
    """A non-blocking, single-threaded SMTP server.

    A server is defined by a request callback that takes an email as an
    argument.
    """

    def __init__(self, request_callback, io_loop=None, **kwargs):
        self.request_callback = request_callback
        TCPServer.__init__(self, io_loop=io_loop, **kwargs)

    def handle_stream(self, stream, address):
        """Handle the stream by executing the request callback.
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
        self.__state = self.COMMAND
        self.__greeting = 0
        self.__mailfrom = None
        self.__rcpttos = []
        self._clear_request_state()
        self._command_callback = stack_context.wrap(self._on_commands)
        self.stream.set_close_callback(self._on_connection_close)
        self.write('220 %s Bonzo SMTP proxy %s' % (self.address[0], version))

    def _clear_request_state(self):
        """Clears the per-request state.

        This is run in between requests to allow the previous handler
        to be garbage collected (and prevent spurious close callbacks),
        and when the connection is closed (to break up cycles and
        facilitate garbage collection in cpython).
        """
        self._request = None
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
        self._header_callback = None
        self._clear_request_state()

    def close(self):
        """Close the stream.
        """
        self.stream.close()
        # Remove this reference to self, which would otherwise cause a
        # cycle and delay garbage collection of this connection.
        self._header_callback = None
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
        line = to_unicode(line)
        if self.__state == self.COMMAND:
            if not line:
                self.write('500 Error: bad syntax')
                return
            i = line.find(' ')
            if i < 0:
                raw_command = line.strip()
                arg = None
            else:
                raw_command = line[:i].strip()
                arg = line[i + 1:].strip()
            method = getattr(self, 'command_' + raw_command.lower(), None)
            if not method:
                self.write('502 Error: command "%s" not implemented' %
                           raw_command)
                return
            method(arg)
        elif self.__state == self.DATA:
            data = []
            for text in line.split(CRLF):
                if text and text[0] == '.':
                    data.append(text[1:])
                else:
                    data.append(text)
            self.__data = '\n'.join(data)
            self.__rcpttos = []
            self.__mailfrom = None
            self.__state = self.COMMAND
            self._on_data(self.__data)
        else:
            self.write('451 Internal confusion')

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

        - Writes a ``501`` error code to the stream when the network name of
          the connecting machine is not received.
        - Writes a ``503`` error code to the stream when a ``HELO`` command
          already was received.
        """
        if not arg:
            self.write('501 Syntax: HELO hostname')
            return
        if self.__greeting:
            self.write('503 Duplicate HELO/EHLO')
        else:
            self.__greeting = arg
            self.write('250 %s' % self.address[0])

    def command_noop(self, arg):
        """Handles the ``NOOP`` SMTP command.

        - Writes a ``501`` error code to the stream when an argument is not
          received.
        """
        if arg:
            self.write('501 Syntax: NOOP')
        else:
            self.write('250 Ok')

    def command_quit(self, arg):
        """Handles the ``QUIT`` SMTP command.
        """
        self.write('221 Bye', self.finish)

    def command_mail(self, arg):
        """Handles the ``MAIL`` SMTP command.

        - Writes a ``501`` error code to the stream when the ``from`` address
          is not received.
        - Writes a ``503`` error code to the stream when a ``MAIL`` command
          already was received.
        """
        address = self.__getaddr('FROM:', arg) if arg else None
        if not address:
            self.write('501 Syntax: MAIL FROM:<address>')
            return
        if self.__mailfrom:
            self.write('503 Error: nested MAIL command')
            return
        self.__mailfrom = address
        self.write('250 Ok')

    def command_rcpt(self, arg):
        """Handles the ``RCPT`` SMTP command.

        - Writes a ``503`` error code to the stream when a ``MAIL`` command was
          not previously received.
        - Writes a ``501`` error code to the stream when the ``to`` address is
          not received.
        """
        if not self.__mailfrom:
            self.write('503 Error: need MAIL command')
            return
        address = self.__getaddr('TO:', arg) if arg else None
        if not address:
            self.write('501 Syntax: RCPT TO:<address>')
            return
        self.__rcpttos.append(address)
        self.write('250 Ok')

    def command_rset(self, arg):
        """Handles the ``RSET`` SMTP command.

        - Writes a ``501`` error code to the stream when an argument is not
          received.
        """
        if arg:
            self.write('501 Syntax: RSET')
            return
        # Resets the sender, recipients, and data, but not the greeting
        self.__mailfrom = None
        self.__rcpttos = []
        self.__data = ''
        self.__state = self.COMMAND
        self.write('250 Ok')

    def command_data(self, arg):
        """Handles the ``DATA`` SMTP command.

        - Writes a ``503`` error code to the stream when a ``RCPT`` command was
          not previously received.
        - Writes a ``501`` error code to the stream when an argument is not
          received.
        """
        if not self.__rcpttos:
            self.write('503 Error: need RCPT command')
            return
        if arg:
            self.write('501 Syntax: DATA')
            return
        self.__state = self.DATA
        self.write('354 End data with <CR><LF>.<CR><LF>',
                   read_until_delimiter='{0}.{0}'.format(CRLF))

    def _on_data(self, data):
        message = email.message_from_string(data)
        self.write("250 Ok")
        self.request_callback(message)
