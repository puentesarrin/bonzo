# -*- coding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from bonzo.testing import AsyncSMTPTestCase


def request_callback(message):
    pass


class AsyncSMTPTestCaseWrapperTest(unittest.TestCase):

    def test_request_callback(self):
        class Test(AsyncSMTPTestCase):

            def get_request_callback(self):
                return request_callback

            def test_pass(self):
                pass

        test = Test('test_pass')
        result = unittest.TestResult()
        test.run(result)
        self.assertEquals(test.get_request_callback(), request_callback)

    def test_request_callback_raise_error(self):
        class Test(AsyncSMTPTestCase):

            def test_pass(self):
                pass

        test = Test('test_pass')
        result = unittest.TestResult()
        test.run(result)
        self.assertRaises(NotImplementedError, test.get_request_callback)
