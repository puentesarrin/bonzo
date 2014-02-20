# -*- coding: utf-8 -*-
from tornado.escape import utf8
from tornado.testing import ExpectLog
from bonzo import errors
from bonzo.mail import Application, RequestHandler
from bonzo.testing import AsyncSMTPTestCase

from tests import server_test


class HandlerSMTPConnectionTest(server_test.SMTPConnectionTest):

    def get_request_callback(self):
        class Handler(RequestHandler):
            pass

        return Application(Handler)


class HandlerSMTPRequestTest(server_test.SMTPRequestTest):

    def get_request_callback(self):
        class Handler(RequestHandler):

            def data(h):
                self.request_mail = h.request.mail
                self.request_rcpt = h.request.rcpt
                self.request_data = h.request.data

        return Application(Handler)


class HandlerSMTPServerTest(server_test.SMTPServerTest):

    def get_request_callback(self):
        class Handler(RequestHandler):

            def data(self):
                raise Exception('This is a custom exception')

        return Application(Handler)


class HandlerErrorTest(server_test.SMTPServerErrorTest):

    def get_request_callback(self):
        class Handler(RequestHandler):

            def data(self):
                raise errors.SMTPError(self.settings['status_code'],
                                       self.settings['message'])

        return Application(Handler, status_code=self.status_code,
                           message=self.message)


class HandlerErrorLogMessageTest(server_test.SMTPServerErrorLogMessageTest):

    def get_request_callback(self):
        class Handler(RequestHandler):

            def data(self):
                raise errors.SMTPError(self.settings['status_code'],
                                       self.settings['message'],
                                       self.settings['log_message'])

        return Application(Handler, status_code=self.status_code,
                           message=self.message, log_message=self.log_message)


class HandlerNotReturnsNoneTest(AsyncSMTPTestCase):

    def get_request_callback(self):
        class Handler(RequestHandler):

            def data(self):
                return True

        return Application(Handler)

    def test_returns_true(self):
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
        with ExpectLog('tornado.application', 'Uncaught exception'):
            self.stream.write(b'This is a message\r\n.\r\n')
            data = self.read_response()
            self.assertEqual(data, b'451 Internal confusion\r\n')
        self.close()


class HandlerWithTwiceFinishTest(AsyncSMTPTestCase):

    def get_request_callback(self):
        class Handler(RequestHandler):

            def data(self):
                self.finish()
                self.finish()

        return Application(Handler)

    def test_twice_finish(self):
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
        with ExpectLog('tornado.application', 'Uncaught exception'):
            self.stream.write(b'This is a message\r\n.\r\n')
            data = self.read_response()
            self.assertEqual(data, b'250 Ok\r\n')
        self.close()
