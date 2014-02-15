# -*- coding: utf-8 -*-
from bonzo import errors
from bonzo.handlers import MessageHandler
from bonzo.testing import AsyncSMTPTestCase

from tests import server_test


class HandlerSMTPConnectionTest(server_test.SMTPConnectionTest):

    def get_request_callback(self):
        class Handler(MessageHandler):
            pass

        return Handler()


class HandlerSMTPRequestTest(server_test.SMTPRequestTest):

    def get_request_callback(self):
        class Handler(MessageHandler):

            def data(h, request):
                self.request_mail = request.mail
                self.request_rcpt = request.rcpt
                self.request_data = request.data
                self.request_message = request.message

        return Handler()


class HandlerSMTPServerTest(server_test.SMTPServerTest):

    def get_request_callback(self):
        class Handler(MessageHandler):

            def data(self, request):
                raise Exception('This is a custom exception')

        return Handler()


class HandlerErrorTest(server_test.SMTPServerErrorTest):

    def get_request_callback(self):
        class Handler(MessageHandler):

            def data(self, request):
                raise errors.SMTPError(self.settings['status_code'],
                                       self.settings['message'])

        return Handler(status_code=self.status_code, message=self.message)


class HandlerErrorLogMessageTest(server_test.SMTPServerErrorLogMessageTest):

    def get_request_callback(self):
        class Handler(MessageHandler):

            def data(self, request):
                raise errors.SMTPError(self.settings['status_code'],
                                       self.settings['message'],
                                       self.settings['log_message'])

        return Handler(status_code=self.status_code, message=self.message,
                       log_message=self.log_message)
