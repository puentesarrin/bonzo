# -*- coding: utf-8 -*-
"""Unit testing support for asynchronous code."""
import socket

from tornado.escape import utf8
from tornado.iostream import IOStream
from tornado.testing import AsyncTestCase, bind_unused_port
from bonzo.server import SMTPServer


class AsyncSMTPTestCase(AsyncTestCase):
    """A test case that starts up an SMTP server.

    Subclasses must override :meth:`get_request_callback()`, which returns a
    :class:`~.server.SMTPServer` callback to be tested.
    """

    def setUp(self):
        super(AsyncSMTPTestCase, self).setUp()
        sock, port = bind_unused_port()
        self.__port = port

        self._request_callback = self.get_request_callback()
        self.smtp_server = self.get_smtp_server()
        self.smtp_server.add_sockets([sock])

    def get_smtp_server(self):
        """Returns an instance of :class:`~.server.SMTPServer` that will be
        used in the test case. It's inmediatelly called when the
        :class:`~.testing.AsyncSMTPTestCase` is instanced.
        """
        return SMTPServer(self._request_callback, io_loop=self.io_loop,
                          **self.get_smtpserver_options())

    def get_request_callback(self):
        """Should be overridden by subclasses to return a
        :class:`~.server.SMTPServer` callback.
        """
        raise NotImplementedError()

    def get_smtpserver_options(self):
        """May be overridden by subclasses to return additional keyword
        arguments for the server.
        """
        return {}

    def get_smtp_port(self):
        """Returns the port used by the server.

        A new port is chosen for each test.
        """
        return self.__port

    def connect(self, read_response=True):
        """Creates a instance of :class:`~tornado.iostream.IOStream` for
        reading and writing bytes to the opened socket on the SMTP server
        address.

        :arg bool read_response: Reads the response of the server immediately
             after to establish connection. Useful to read the response and
             discard the welcome message.
        """
        self.stream = IOStream(socket.socket(), io_loop=self.io_loop)
        self.stream.connect(('localhost', self.get_smtp_port()), self.stop)
        self.wait()
        if read_response:
            self.read_response()

    def read_response(self):
        """Reads the response of the stream.
        """
        self.stream.read_until(b'\r\n', self.stop)
        return self.wait()

    def send_mail(self, hostname, mail, rcpt, data):
        """Sends a coherent sequence of command to send a message. Returns the
        result from the ``DATA`` command.
        """
        self.stream.write(utf8('HELO %s\r\n' % hostname))
        self.read_response()
        self.stream.write(utf8('MAIL FROM:%s\r\n' % mail))
        self.read_response()
        for address in rcpt:
            self.stream.write(utf8('RCPT TO:%s\r\n' % address))
            self.read_response()
        self.stream.write(b'DATA\r\n')
        self.read_response()
        self.stream.write(utf8('%s\r\n.\r\n' % data))
        return self.read_response()

    def close(self):
        """Closes the stream.
        """
        self.stream.close()
        del self.stream

    def tearDown(self):
        self.smtp_server.stop()
        super(AsyncSMTPTestCase, self).tearDown()
