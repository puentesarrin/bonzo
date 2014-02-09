# -*- coding: utf-8 -*-
"""Bonzo is a SMTP Server built on top of Tornado."""
import sys

if sys.version_info[0] >= 3:
    basestring_type = str  # pragma: no cover
else:
    basestring_type = basestring  # pragma: no cover


version_tuple = (0, 1, 2, '+')


def get_version_string():
    if isinstance(version_tuple[-1], basestring_type):
        return '.'.join(map(str, version_tuple[:-1])) + version_tuple[-1]
    return '.'.join(map(str, version_tuple))

version = get_version_string()
"""Current version of Bonzo."""

__author__ = 'Jorge Puente Sarrín <puentesarrin@gmail.com>'
__since__ = '2013-08-21'
__version__ = version
