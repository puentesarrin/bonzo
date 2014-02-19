.. Bonzo documentation master file, created by
   sphinx-quickstart on Wed Feb  5 15:27:08 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Bonzo: SMTP Server built on top of Tornado
==========================================

.. image:: _static/bonzo_sigil.png
   :align: center
   :alt: John Bonham's sigil three intersecting circles

About
-----

Bonzo is a Python SMTP Server using the asynchronous network library of
Tornado_. And it's actually a port of Python's smtpd_ module.

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

Hello, world
------------

Here is a simple "Hello, world" example SMTP server for Bonzo:

.. code-block:: python

   from tornado.ioloop import IOLoop
   from bonzo.server import SMTPServer


   def handle_request(request):
       print(request.message)
       request.finish()

   SMTPServer(handle_request).listen(2525)
   IOLoop.current().start()

Installation
============

You can to use pip_ to install Bonzo:

.. code-block:: bash

   $ pip install bonzo

Or using last source:

.. code-block:: bash

   $ pip install git+https://github.com/puentesarrin/bonzo.git

License
=======

Bonzo is available under the |apache-license|_.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. note::

   **Logo credits:** Image created by Freakofnurture_ (Wikimedia user),
   released into the public domain (|image-source|_).

.. toctree::
   :hidden:

   modules/index
   releases/index
   contributors

.. _Tornado: http://tornadoweb.org
.. _smtpd: http://docs.python.org/library/smtpd.html
.. _pip: http://pypi.python.org/pypi/pip
.. _apache-license: http://www.apache.org/licenses/LICENSE-2.0.html
.. |apache-license| replace:: Apache License, Version 2.0
.. _Freakofnurture: http://commons.wikimedia.org/wiki/User:Freakofnurture
.. _image-source: http://commons.wikimedia.org/wiki/File:Zoso_John_Bonham_sigil_three_intersecting_circles.svg
.. |image-source| replace:: source
