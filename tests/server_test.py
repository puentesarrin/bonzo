# -*- coding: utf-8 -*-
import email

from tornado.escape import to_unicode, utf8
from tornado.testing import ExpectLog
from bonzo import errors, version
from bonzo.testing import AsyncSMTPTestCase


class SMTPConnectionTest(AsyncSMTPTestCase):

    def get_request_callback(self):

        def request_callback(request):
            request.finish()
        return request_callback

    def test_welcome_connection(self):
        self.connect(read_response=False)
        data = self.read_response()
        self.assertEqual(data, utf8('220 Bonzo SMTP Server %s\r\n' % version))
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
        self.assertEqual(data, b'250 Hello 127.0.0.1\r\n')
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
        self.read_response()
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
        self.stream.write(b'HELO NameClient\r\n')
        self.read_response()
        self.stream.write(b'QUIT\r\n')
        data = self.read_response()
        self.assertEqual(data, b'221 Bye\r\n')
        self.close()

    def test_mail(self):
        for address in ['mail@example.com', '<mail@example.com>']:
            self.connect()
            self.stream.write(b'HELO NameClient\r\n')
            self.read_response()
            self.stream.write(utf8('MAIL FROM:%s\r\n' % address))
            data = self.read_response()
            self.assertEqual(data, b'250 Ok\r\n')
            self.close()

    def test_mail_without_helo(self):
        self.connect()
        self.stream.write(utf8('MAIL FROM:mail@example.com\r\n'))
        data = self.read_response()
        self.assertEqual(data, b'503 Error: need HELO command\r\n')
        self.close()

    def test_mail_without_address(self):
        self.connect()
        self.stream.write(b'HELO NameClient\r\n')
        self.read_response()
        self.stream.write(b'MAIL FROM:\r\n')
        data = self.read_response()
        self.assertEqual(data, b'501 Syntax: MAIL FROM:<address>\r\n')
        self.close()

    def test_duplicate_mail(self):
        self.connect()
        self.stream.write(b'HELO NameClient\r\n')
        self.read_response()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        self.read_response()
        self.stream.write(b'MAIL FROM:anothermail@example.com\r\n')
        data = self.read_response()
        self.assertEqual(data, b'503 Error: nested MAIL command\r\n')
        self.close()

    def test_rcpt(self):
        for address in ['mail@example.com', '<mail@example.com>']:
            self.connect()
            self.stream.write(b'HELO NameClient\r\n')
            self.read_response()
            self.stream.write(b'MAIL FROM:mail@example.com\r\n')
            self.read_response()
            self.stream.write(utf8('RCPT TO:%s\r\n' % address))
            data = self.read_response()
            self.assertEqual(data, b'250 Ok\r\n')
            self.close()

    def test_rcpt_without_address(self):
        self.connect()
        self.stream.write(b'HELO NameClient\r\n')
        self.read_response()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        self.read_response()
        self.stream.write(b'RCPT TO:\r\n')
        data = self.read_response()
        self.assertEqual(data, b'501 Syntax: RCPT TO:<address>\r\n')
        self.close()

    def test_rcpt_without_mail(self):
        self.connect()
        self.stream.write(b'RCPT TO:mail@example.com\r\n')
        data = self.read_response()
        self.assertEqual(data, b'503 Error: need MAIL command\r\n')
        self.close()

    def test_rcpt_multiple_adressess(self):
        self.connect()
        self.stream.write(b'HELO NameClient\r\n')
        self.read_response()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        self.read_response()
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
        self.stream.write(b'HELO NameClient\r\n')
        self.read_response()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        self.read_response()
        for address in ['mail@example.com', '<mail@example.com>']:
            self.stream.write(utf8('RCPT TO:%s\r\n' % address))
            self.read_response()
        self.stream.write(b'DATA\r\n')
        data = self.read_response()
        self.assertEqual(data, b'354 End data with <CR><LF>.<CR><LF>\r\n')
        self.stream.write(b'This is a message\r\n.\r\n')
        data = self.read_response()
        self.assertEqual(data, b'250 Ok\r\n')
        self.close()

    def test_data_without_mail(self):
        self.connect()
        self.stream.write(b'DATA\r\n')
        data = self.read_response()
        self.assertEqual(data, b'503 Error: need RCPT command\r\n')
        self.close()

    def test_data_without_rcpt(self):
        self.connect()
        self.stream.write(b'HELO NameClient\r\n')
        self.read_response()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        self.read_response()
        self.stream.write(b'DATA\r\n')
        data = self.read_response()
        self.assertEqual(data, b'503 Error: need RCPT command\r\n')
        self.close()

    def test_data_with_arguments(self):
        self.connect()
        self.stream.write(b'HELO NameClient\r\n')
        self.read_response()
        self.stream.write(b'MAIL FROM:mail@example.com\r\n')
        self.read_response()
        for address in ['mail@example.com', '<mail@example.com>']:
            self.stream.write(utf8('RCPT TO:%s\r\n' % address))
            self.read_response()
        self.stream.write(b'DATA args\r\n')
        data = self.read_response()
        self.assertEqual(data, b'501 Syntax: DATA\r\n')
        self.close()


class SMTPRequestTest(AsyncSMTPTestCase):

    def setUp(self):
        self.hostname = 'client'
        self.mail = 'mail@example.com'
        self.rcpt = ['mail@example.com', 'anothermail@example.com']
        self.data = 'This is a message.'
        self.message = email.message_from_string(to_unicode(self.data))
        super(SMTPRequestTest, self).setUp()

    def get_request_callback(self):

        def request_callback(request):
            self.request_mail = request.mail
            self.request_rcpt = request.rcpt
            self.request_data = request.data
            self.request_message = request.message
            self.request_repr = '%s' % request
            request.finish()
        return request_callback

    def test_request_object(self):
        self.connect()
        data = self.send_mail(self.hostname, self.mail, self.rcpt, self.data)
        self.assertEqual(data, b'250 Ok\r\n')
        self.assertEqual(self.mail, self.request_mail)
        self.assertEqual(self.rcpt, self.request_rcpt)
        self.assertEqual(self.data, self.request_data)
        self.assertEqual(self.message.as_string(),
                         self.request_message.as_string())
        self.assertTrue(("remote_ip='127.0.0.1'") in self.request_repr)
        self.assertTrue(("hostname='%s'" % self.hostname) in self.request_repr)
        self.assertTrue(("mail='%s'" % self.mail) in self.request_repr)
        self.assertTrue(("rcpt='%s'" % [to_unicode(r) for r in self.rcpt])
                        in self.request_repr)
        self.close()


class SMTPServerTest(AsyncSMTPTestCase):

    def get_request_callback(self):

        def request_callback(request):
            raise Exception('This is a custom exception')
        return request_callback

    def test_internal_confusion(self):
        self.connect()
        with ExpectLog('tornado.application', 'Uncaught exception'):
            data = self.send_mail('client', 'mail@example.com',
                                  ['mail@example.com', '<mail@example.com>'],
                                  'This is a message')
            self.assertEqual(data, b'451 Internal confusion\r\n')
        self.close()


class SMTPServerErrorTest(AsyncSMTPTestCase):

    def setUp(self):
        self.status_code = 452
        self.message = 'Insufficient system storage'
        super(SMTPServerErrorTest, self).setUp()

    def get_request_callback(self):
        def request_callback(message):
            raise errors.SMTPError(self.status_code, self.message)
        return request_callback

    def test_logged_smtp_error(self):
        self.connect()
        data = self.send_mail('client', 'mail@example.com',
                              ['mail@example.com', '<mail@example.com>'],
                              'This is a message')
        self.assertEqual(data, utf8('%d %s\r\n' % (self.status_code,
                                                   self.message)))
        self.close()


class SMTPServerErrorLogMessageTest(AsyncSMTPTestCase):

    def setUp(self):
        self.status_code = 452
        self.message = 'Insufficient system storage'
        self.log_message = 'This is a custom message to be logged'
        super(SMTPServerErrorLogMessageTest, self).setUp()

    def get_request_callback(self):
        def request_callback(request):
            raise errors.SMTPError(self.status_code, self.message,
                                   self.log_message)
        return request_callback

    def test_logged_smtp_error_with_message(self):
        self.connect()
        with ExpectLog('tornado.general', r'.*%d %s' % (self.status_code,
                                                        self.log_message)):
            data = self.send_mail('client', 'mail@example.com',
                                  ['mail@example.com', '<mail@example.com>'],
                                  'This is a message')
            self.assertEqual(data, utf8('%d %s\r\n' % (self.status_code,
                                                       self.message)))
        self.close()
