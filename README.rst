=====
Bonzo
=====

.. image:: https://bonzo.readthedocs.org/en/latest/_images/bonzo_sigil.png
   :align: center
   :alt: John Bonham's sigil three intersecting circles

About
=====

Bonzo is a Python SMTP Server using the asynchronous network library of
Tornado_. And it's actually a port of Python's smtpd_ module

Bonzo is a SMTP Server built on top of Tornado_.

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
============

.. code-block:: python

   from tornado.ioloop import IOLoop
   from bonzo.server import SMTPServer


   def handle_request(request):
       print(request.message)
       request.finish()

   SMTPServer(handle_request).listen(25)
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

.. _Tornado: http://tornadoweb.org
.. _pip: http://pypi.python.org/pypi/pip
.. _smtpd: http://docs.python.org/library/smtpd.html
.. _apache-license: http://www.apache.org/licenses/LICENSE-2.0.html
.. |apache-license| replace:: Apache Licence, Version 2.0
