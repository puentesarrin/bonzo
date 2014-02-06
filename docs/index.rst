.. Bonzo documentation master file, created by
   sphinx-quickstart on Wed Feb  5 15:27:08 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Bonzo |release| documentation
=============================

.. image:: https://travis-ci.org/puentesarrin/bonzo.png
   :target: https://travis-ci.org/puentesarrin/bonzo
   :alt: Travis CI status

.. image:: https://coveralls.io/repos/puentesarrin/bonzo/badge.png
   :target: https://coveralls.io/r/puentesarrin/bonzo
   :alt: Coveralls status

.. image:: https://pypip.in/v/bonzo/badge.png
   :target: https://pypi.python.org/pypi/bonzo
   :alt: Latest PyPI version

.. image:: https://pypip.in/d/bonzo/badge.png
   :target: https://pypi.python.org/pypi/bonzo
   :alt: Number of PyPI downloads

Bonzo is a minimalistic Python SMTP server. It's really a port of Python's
smtpd_ using the asynchronous network library of Tornado_.

Hello, world
------------

Here is a simple “Hello, world” example SMTP server for Bonzo:

.. code-block:: python

   from tornado.ioloop import IOLoop
   from bonzo.server import SMTPServer


   def receive_message(message):
       print(message)

   SMTPServer(receive_message).listen(2525)
   IOLoop.instance().start()

Installation
============

You can to use pip_ to install Bonzo:

.. code-block:: bash

   $ pip install bonzo

Or using last source:

.. code-block:: bash

   $ pip install git+https://github.com/puentesarrin/bonzo.git

.. toctree::
   :hidden:

   modules/index
   releases/index
   contributors

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _pip: http://pypi.python.org/pypi/pip
.. _smtpd: http://docs.python.org/library/smtpd.html
.. _Tornado: http://tornadoweb.org