# -*- coding: utf-8 -*-
from tornado.escape import utf8
from tornado.testing import ExpectLog, LogTrapTestCase
from bonzo import errors, version
from bonzo.testing import AsyncSMTPTestCase


class SMTPConnectionTest(AsyncSMTPTestCase):

    def get_request_callback(self):

        def request_callback(message):
            pass
        return request_callback

    def test_welcome_connection(self):
        self.connect(read_response=False)
        data = self.read_response()
        self.assertEqual(data, utf8('220 127.0.0.1 Bonzo SMTP proxy %s\r\n' %
                                    version))
        self.close()

    def test_not_implemented_command(self):
        self.connect()
        for command in ['BADCOMMAND', 'unknown', 'Bonzo']:
            self.stream.write(utf8('%s\r\n' % command))
            data = self.read_response()
            self.assertEqual(data, utf8('502 Error: command "%s" not '
                                        'implemented\r\n' % command))
        self.close()

    def test_unrecognised_command(self):
        self.connect()
        for command in ['', '  ']:
            self.stream.write(utf8('%s\r\n' % command))
            data = self.read_response()
            self.assertEqual(data, utf8('500 Error: bad syntax\r\n'))
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
            self.stream.write(utf8('MAIL FROM:%s\r\n' % address))
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
            self.stream.write(utf8('RCPT TO:%s\r\n' % address))
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
            self.stream.write(utf8('RCPT TO:%s\r\n' % address))
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
            self.stream.write(utf8('RCPT TO:%s\r\n' % address))
            data = self.read_response()
            self.assertEqual(data, b'250 Ok\r\n')
        self.stream.write(b'DATA\r\n')
        data = self.read_response()
        self.assertEqual(data, b'354 End data with <CR><LF>.<CR><LF>\r\n')
        self.stream.write(b'This is a message\r\n.\r\n')
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
            self.stream.write(utf8('RCPT TO:%s\r\n' % address))
            data = self.read_response()
            self.assertEqual(data, b'250 Ok\r\n')
        self.stream.write(b'DATA args\r\n')
        data = self.read_response()
        self.assertEqual(data, b'501 Syntax: DATA\r\n')
        self.close()


class SMTPServerTest(AsyncSMTPTestCase):

    def get_request_callback(self):

        def request_callback(message):
            raise Exception('This is a custom exception')
        return request_callback

    def test_internal_confusion(self):
        self.connect()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        self.read_response()
        for address in ['mail@example.com', '<mail@example.com>']:
            self.stream.write(utf8('RCPT TO:%s\r\n' % address))
            self.read_response()
        self.stream.write(b'DATA\r\n')
        self.read_response()
        with ExpectLog('tornado.application', 'Uncaught exception'):
            self.stream.write(b'This is a message\r\n.\r\n')
            data = self.read_response()
            self.assertEqual(data, b'451 Internal confusion\r\n')
        self.close()


class SMTPServerErrorTest(AsyncSMTPTestCase):

    def get_request_callback(self):
        self.status_code = 452
        self.message = 'Insufficient system storage'

        def request_callback(message):
            raise errors.SMTPError(self.status_code, self.message)
        return request_callback

    def test_logged_smtp_error(self):
        self.connect()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        self.read_response()
        for address in ['mail@example.com', '<mail@example.com>']:
            self.stream.write(utf8('RCPT TO:%s\r\n' % address))
            self.read_response()
        self.stream.write(b'DATA\r\n')
        self.read_response()
        self.stream.write(b'This is a message\r\n.\r\n')
        data = self.read_response()
        self.assertEqual(data, utf8('%d %s\r\n' % (self.status_code,
                                                   self.message)))
        self.close()


class SMTPServerErrorLogMessageTest(AsyncSMTPTestCase):

    def get_request_callback(self):
        self.status_code = 452
        self.message = 'Insufficient system storage'
        self.log_message = 'This is a custom message to be logged'

        def request_callback(message):
            raise errors.SMTPError(self.status_code, self.message,
                                   self.log_message)
        return request_callback

    def test_logged_smtp_error_with_message(self):
        self.connect()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        self.read_response()
        for address in ['mail@example.com', '<mail@example.com>']:
            self.stream.write(utf8('RCPT TO:%s\r\n' % address))
            self.read_response()
        self.stream.write(b'DATA\r\n')
        self.read_response()
        with ExpectLog('tornado.general', r'.*%d %s' % (self.status_code,
                                                        self.log_message)):
            self.stream.write(b'This is a message\r\n.\r\n')
            data = self.read_response()
            self.assertEqual(data, utf8('%d %s\r\n' % (self.status_code,
                                                       self.message)))
        self.close()
