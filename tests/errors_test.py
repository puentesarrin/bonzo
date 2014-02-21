# -*- coding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from bonzo import errors


class SMTPErrorTest(unittest.TestCase):

    def setUp(self):
        self.status_code = 501
        self.message = 'This is a message exception.'
        self.log_message = 'This is a %s_%s with %r.'
        self.args = ('log', 'message', 'format')

    def test_str(self):
        e = errors.SMTPError(self.status_code, self.message)
        self.assertEqual(str(e), 'SMTP %d: %s' % (self.status_code,
                                                  self.message))

    def test_str_with_log_message(self):
        e = errors.SMTPError(self.status_code, self.message, self.log_message,
                             *self.args)
        self.assertEqual(str(e),
                         'SMTP %d: %s (%s)' % (self.status_code, self.message,
                                               (self.log_message % self.args)))

    def test_internal_confusion_error(self):
        e = errors.InternalConfusion()
        self.assertEqual(str(e), 'SMTP %d: %s' % (451, 'Internal confusion'))

    def test_unrecognised_command_error(self):
        e = errors.UnrecognisedCommand()
        self.assertEqual(str(e), 'SMTP %d: %s' % (500, 'Error: bad syntax'))
