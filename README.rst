=====
Bonzo
=====

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

About
=====

Bonzo is a SMTP Server built on top of Tornado_.

.. code-block:: python

   import tornado.ioloop
   import email

   from bonzo.server import SMTPServer


   def receive_message(message):
       print "New received message: "
       print "From: " + message['from']
       print "Subject: " + message['subject']
       for line in email.iterators.body_line_iterator(message):
           print line

   SMTPServer(receive_message).listen(25)
   tornado.ioloop.IOLoop.instance().start()

Installation
============

You can to use pip_ to install Bonzo::

   $ pip install bonzo

Or using last source::

   $ pip install git+git://github.com/puentesarrin/bonzo.git

.. _Tornado: http://tornadoweb.org
.. _pip: http://pypi.python.org/pypi/pip
