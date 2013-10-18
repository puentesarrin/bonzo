# -*- coding: utf-8 -*-
import email
import functools

from tornado.tcpserver import TCPServer
from tornado import stack_context

from bonzo import version

CRLF = '\r\n'


class SMTPServer(TCPServer):

    def __init__(self, request_callback, io_loop=None, **kwargs):
        self.request_callback = request_callback
        TCPServer.__init__(self, io_loop=io_loop, **kwargs)

    def handle_stream(self, stream, address):
        SMTPConnection(stream, address, self.request_callback)


class SMTPConnection(object):

    COMMAND = 0
    DATA = 1

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

        Use this instead of accessing
        `SMTPConnection.stream.set_close_callback
        <.BaseIOStream.set_close_callback>` directly (which was the
        recommended approach prior to Tornado 3.0).
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
                                             read_until_delimiter,
                                             self._on_commands)
            self._write_callback = stack_context.wrap(callback)
            self.stream.write(chunk + CRLF, self._on_write_complete)

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
        if self.__state == self.COMMAND:
            if not line:
                self.write('500 Error: bad syntax')
                return
            i = line.find(' ')
            if i < 0:
                command = line.lower()
                arg = None
            else:
                command = line[:i].lower()
                arg = line[i + 1:].strip()
            method = getattr(self, 'command_' + command.strip(), None)
            if not method:
                self.write('502 Error: command "%s" not implemented' % command)
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
        if not arg:
            self.write('501 Syntax: HELO hostname')
            return
        if self.__greeting:
            self.write('503 Duplicate HELO/EHLO')
        else:
            self.__greeting = arg
            self.write('250 %s' % self.address[0])

    def command_noop(self, arg):
        if arg:
            self.write('501 Syntax: NOOP')
        else:
            self.write('250 Ok')

    def command_quit(self, arg):
        self.write('221 Bye', self.finish)

    def command_mail(self, arg):
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
        if not self.__mailfrom:
            self.write('503 Error: need MAIL command')
            return
        address = self.__getaddr('TO:', arg) if arg else None
        if not address:
            self.write('501 Syntax: RCPT TO: <address>')
            return
        self.__rcpttos.append(address)
        self.write('250 Ok')

    def command_rset(self, arg):
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
