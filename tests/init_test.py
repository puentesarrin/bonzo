# -*- coding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import bonzo


class InitTest(unittest.TestCase):

    def test_version_string(self):
        bonzo.version_tuple = (0, 0, 0)
        self.assertEquals(bonzo.get_version_string(), '0.0.0')
        bonzo.version_tuple = (1, 0, 0)
        self.assertEquals(bonzo.get_version_string(), '1.0.0')
        bonzo.version_tuple = (5, 0, '+')
        self.assertEquals(bonzo.get_version_string(), '5.0+')
        bonzo.version_tuple = (0, 4, 'b')
        self.assertEquals(bonzo.get_version_string(), '0.4b')
