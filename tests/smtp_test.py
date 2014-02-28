# -*- coding: utf-8 -*-
from tornado import gen
from tornado.testing import ExpectLog
from bonzo import errors
from bonzo.smtp import Application, RequestHandler
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
                self.request_message = h.request.message
                self.request_repr = '%s' % h.request

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
        with ExpectLog('tornado.application', 'Uncaught exception'):
            data = self.send_mail('client', 'mail@example.com',
                                  ['mail@example.com', '<mail@example.com>'],
                                  'This is a message')
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
        with ExpectLog('tornado.application', 'Uncaught exception'):
            data = self.send_mail('client', 'mail@example.com',
                                  ['mail@example.com', '<mail@example.com>'],
                                  'This is a message')
            self.assertEqual(data, b'250 Ok\r\n')
        self.close()


class HandlerCoroutineTest(AsyncSMTPTestCase):

    def setUp(self):
        self.coroutine_result = 'result from coroutine'
        super(HandlerCoroutineTest, self).setUp()

    def get_request_callback(self):
        class Handler(RequestHandler):

            @gen.coroutine
            def coroutine_decorated(h):
                raise gen.Return(self.coroutine_result)

            @gen.coroutine
            def data(h):
                self.data_result = yield h.coroutine_decorated()

        return Application(Handler)

    def test_coroutine_on_data(self):
        self.connect()
        self.send_mail('client', 'mail@example.com',
                       ['mail@example.com', '<mail@example.com>'],
                       'This is a message')
        self.assertEqual(self.data_result, self.coroutine_result)
        self.close()
