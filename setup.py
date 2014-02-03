# -*- coding: utf-8 *-*
import os

try:
    from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

from bonzo import __version__


with open('README.rst') as f:
    readme_content = f.read()

setup(
    name='bonzo',
    version=__version__,
    url='https://github.com/puentesarrin/bonzo',
    description='Bonzo is a minimalistic SMTP Proxy built on top of Tornado.',
    long_description=readme_content,
    author=u'Jorge Puente Sarrín',
    author_email='puentesarrin@gmail.com',
    packages=['bonzo'],
    keywords=['bonzo', 'tornado', 'smtp', 'proxy'],
    install_requires=['tornado >= 3.0'],
    license='Apache License, Version 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: Proxy Servers'],
    test_suite='tests.runtests',
)
