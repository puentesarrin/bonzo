# -*- coding: utf-8 -*-
"""Bonzo is a minimalistic SMTP Proxy built on top of Tornado."""
import sys

if sys.version_info[0] >= 3:
    basestring_type = str
else:
    basestring_type = basestring


version_tuple = (0, 1, 1, '+')


def get_version_string():
    if isinstance(version_tuple[-1], basestring_type):
        return '.'.join(map(str, version_tuple[:-1])) + version_tuple[-1]
    return '.'.join(map(str, version_tuple))

version = get_version_string()
"""Current version of Bonzo."""

__author__ = 'Jorge Puente Sarrín <puentesarrin@gmail.com>'
__since__ = '2013-08-21'
__version__ = version
