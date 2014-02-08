.. Bonzo documentation master file, created by
   sphinx-quickstart on Wed Feb  5 15:27:08 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Bonzo: SMTP Proxy built on top of Tornado
=========================================

.. image:: _static/bonzo_sigil.png
   :align: center
   :alt: John Bonham sigil three intersecting circles

About
-----

Bonzo is a Python SMTP Proxy. It's actually a port of Python's smtpd_ using
the asynchronous network library of Tornado_.

Bonzo is available under the |apache-license|_.

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

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. note::

   Logo credits: Image by Freakofnurture_ (Wikimedia user), released into the
   public domain (|image-source|_).

.. toctree::
   :hidden:

   modules/index
   releases/index
   contributors

.. _pip: http://pypi.python.org/pypi/pip
.. _smtpd: http://docs.python.org/library/smtpd.html
.. _Tornado: http://tornadoweb.org
.. _apache-license: http://www.apache.org/licenses/LICENSE-2.0.html
.. |apache-license| replace:: Apache Licence, Version 2.0
.. _Freakofnurture: http://commons.wikimedia.org/wiki/User:Freakofnurture
.. _image-source: http://commons.wikimedia.org/wiki/File:Zoso_John_Bonham_sigil_three_intersecting_circles.svg
.. |image-source| replace:: source
