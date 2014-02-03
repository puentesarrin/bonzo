
import socket

from tornado.iostream import IOStream
from bonzo import version
from bonzo.testing import AsyncSMTPTestCase


def request_callback(message):
    print(message)


class SMTPServerTest(AsyncSMTPTestCase):

    def get_request_callback(self):
        return request_callback

    def tearDown(self):
        super(SMTPServerTest, self).tearDown()

    def connect(self, read_response=True):
        self.stream = IOStream(socket.socket(), io_loop=self.io_loop)
        self.stream.connect(('localhost', self.get_smtp_port()), self.stop)
        self.wait()
        # If needed, read the response to discard the welcome message.
        if read_response:
            self.read_response()

    def read_response(self):
        self.stream.read_until(b'\r\n', self.stop)
        return self.wait()

    def close(self):
        self.stream.close()
        del self.stream

    def test_welcome_connection(self):
        self.connect(read_response=False)
        data = self.read_response()
        self.assertEqual(data,
                         b'220 127.0.0.1 Bonzo SMTP proxy %s\r\n' % version)
        self.close()

    def test_not_implemented_command(self):
        self.connect()
        for command in [b'BADCOMMAND', b'UNKNOWN', b'BONZO']:
            self.stream.write(b'%s\r\n' % command)
            data = self.read_response()
            self.assertEqual(data, b'502 Error: command "%s" not implemented' %
                                   command)
        self.close()

    def test_helo(self):
        self.connect()
        self.stream.write(b'HELO Client name\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 127.0.0.1\r\n')
        self.close()

    def test_helo_without_hostname(self):
        self.connect()
        self.stream.write(b'HELO\r\n')
        data = self.read_response()
        self.assertEqual(data, b'501 Syntax: HELO hostname\r\n')
        self.close()

    def test_duplicate_helo(self):
        self.connect()
        self.stream.write(b'HELO NameClient\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 127.0.0.1\r\n')
        self.stream.write(b'HELO NameClient\r\n')
        data = self.read_response()
        self.assertEqual(data, b'503 Duplicate HELO/EHLO\r\n')
        self.close()

    def test_noop(self):
        self.connect()
        self.stream.write(b'NOOP\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 Ok\r\n')
        self.close()

    def test_noop_with_arguments(self):
        self.connect()
        self.stream.write(b'NOOP args\r\n')
        data = self.read_response()
        self.assertEqual(data, b'501 Syntax: NOOP\r\n')
        self.close()

    def test_quit(self):
        self.connect()
        self.stream.write(b'QUIT\r\n')
        data = self.read_response()
        self.assertEqual(data, b'221 Bye\r\n')
        self.close()

    def test_from(self):
        for address in ['mail@example.com', '<mail@example.com>']:
            self.connect()
            self.stream.write(b'MAIL FROM:%s\r\n' % address)
            data = self.read_response()
            self.assertEqual(data, b'250 Ok\r\n')
            self.close()

    def test_from_without_address(self):
        self.connect()
        self.stream.write(b'MAIL FROM:\r\n')
        data = self.read_response()
        self.assertEqual(data, b'501 Syntax: MAIL FROM:<address>\r\n')
        self.close()

    def test_duplicate_from(self):
        self.connect()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 Ok\r\n')
        self.stream.write(b'MAIL FROM:anothermail@example.com\r\n')
        data = self.read_response()
        self.assertEqual(data, b'503 Error: nested MAIL command\r\n')
        self.close()

    def test_rcpt(self):
        for address in ['mail@example.com', '<mail@example.com>']:
            self.connect()
            self.stream.write(b'MAIL FROM:mail@example.com\r\n')
            data = self.read_response()
            self.assertEqual(data, b'250 Ok\r\n')
            self.stream.write(b'RCPT TO:%s\r\n' % address)
            data = self.read_response()
            self.assertEqual(data, b'250 Ok\r\n')
            self.close()

    def test_rcpt_without_address(self):
        self.connect()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 Ok\r\n')
        self.stream.write(b'RCPT TO:\r\n')
        data = self.read_response()
        self.assertEqual(data, b'501 Syntax: RCPT TO:<address>\r\n')
        self.close()

    def test_rcpt_without_from(self):
        self.connect()
        self.stream.write(b'RCPT TO:mail@example.com\r\n')
        data = self.read_response()
        self.assertEqual(data, b'503 Error: need MAIL command\r\n')
        self.close()

    def test_rcpt_multiple_adressess(self):
        self.connect()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 Ok\r\n')
        for address in ['mail@example.com', '<mail@example.com>']:
            self.stream.write(b'RCPT TO:%s\r\n' % address)
            data = self.read_response()
            self.assertEqual(data, b'250 Ok\r\n')
        self.close()

    def test_rset(self):
        self.connect()
        self.stream.write(b'RSET\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 Ok\r\n')
        self.close()

    def test_rset_with_arguments(self):
        self.connect()
        self.stream.write(b'RSET args\r\n')
        data = self.read_response()
        self.assertEqual(data, b'501 Syntax: RSET\r\n')
        self.close()

    def test_data(self):
        self.connect()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 Ok\r\n')
        for address in ['mail@example.com', '<mail@example.com>']:
            self.stream.write(b'RCPT TO:%s\r\n' % address)
            data = self.read_response()
            self.assertEqual(data, b'250 Ok\r\n')
        self.stream.write(b'DATA\r\n')
        data = self.read_response()
        self.assertEqual(data, b'354 End data with <CR><LF>.<CR><LF>\r\n')
        self.stream.write('This is a message\r\n.\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 Ok\r\n')
        self.close()

    def test_data_without_from(self):
        self.connect()
        self.stream.write(b'DATA\r\n')
        data = self.read_response()
        self.assertEqual(data, b'503 Error: need RCPT command\r\n')
        self.close()

    def test_data_without_rcpt(self):
        self.connect()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 Ok\r\n')
        self.stream.write(b'DATA\r\n')
        data = self.read_response()
        self.assertEqual(data, b'503 Error: need RCPT command\r\n')
        self.close()

    def test_data_with_arguments(self):
        self.connect()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 Ok\r\n')
        for address in ['mail@example.com', '<mail@example.com>']:
            self.stream.write(b'RCPT TO:%s\r\n' % address)
            data = self.read_response()
            self.assertEqual(data, b'250 Ok\r\n')
        self.stream.write(b'DATA args\r\n')
        data = self.read_response()
        self.assertEqual(data, b'501 Syntax: DATA\r\n')
        self.close()
