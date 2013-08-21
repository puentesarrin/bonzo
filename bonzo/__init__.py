# -*- coding: utf-8 -*-
"""Bonzo is a minimalistic SMTP Proxy built on top of Tornado."""


version_tuple = (0, 1)


def get_version_string():
    if isinstance(version_tuple[-1], basestring):
        return '.'.join(map(str, version_tuple[:-1])) + version_tuple[-1]
    return '.'.join(map(str, version_tuple))

version = get_version_string()
"""Current version of Bonzo."""

__author__ = 'Jorge Puente Sarrín <puentesarrin@gmail.com>'
__since__ = '2013-08-21'
__version__ = version
