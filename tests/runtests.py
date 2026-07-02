import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    suite = unittest.defaultTestLoader.discover('tests', pattern='*_test.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return int(not result.wasSuccessful())


if __name__ == '__main__':
    sys.exit(main())
