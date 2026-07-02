=====
Bonzo
=====

.. image:: https://github.com/puentesarrin/bonzo/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/puentesarrin/bonzo/actions/workflows/ci.yml
   :alt: CI status

.. image:: https://coveralls.io/repos/github/puentesarrin/bonzo/badge.svg?branch=master
   :target: https://coveralls.io/github/puentesarrin/bonzo?branch=master
   :alt: Coverage status

.. image:: https://bonzo.readthedocs.io/en/latest/_images/bonzo_sigil.png
   :align: center
   :alt: John Bonham's sigil three intersecting circles

About
=====

Bonzo is an asynchronous SMTP server built on Tornado_. It started as
a port of Python's old smtpd_ module and now uses Tornado's native
async/await APIs.

Hello, world
============

Here is a simple "Hello, world" example SMTP server for Bonzo:

.. code-block:: python

   import asyncio
   import bonzo.smtp


   class Handler(bonzo.smtp.RequestHandler):

       async def data(self):
           print(self.request.message)


   async def main():
       application = bonzo.smtp.Application(Handler)
       application.listen(2525)
       await asyncio.Event().wait()


   if __name__ == '__main__':
       asyncio.run(main())

Installation
============

Use pip_ to install Bonzo:

.. code-block:: bash

   $ pip install bonzo

Or install from the latest source:

.. code-block:: bash

   $ pip install git+https://github.com/puentesarrin/bonzo.git

Documentation
=============

Sphinx_ is needed to generate the documentation:

.. code-block:: bash

   $ python -m sphinx -W --keep-going -b html docs docs/_build/html

Install the development tools and run the test suite with tox_:

.. code-block:: bash

   $ python -m pip install -e ".[dev]"
   $ tox

Run the same tests directly with unittest:

.. code-block:: bash

   $ python -m unittest discover -s tests -p '*_test.py'

To test against specific Python interpreters installed on your machine:

.. code-block:: bash

   $ tox -e py39,py310,py311,py312,py313,pypy3

Also, the current documentation can be found at ReadTheDocs_.

License
=======

Bonzo is available under the |apache-license|_.

.. note::

   **Logo credits:** Image created by Freakofnurture_ (Wikimedia user),
   released into the public domain (|image-source|_).

.. _Tornado: https://www.tornadoweb.org/
.. _smtpd: https://docs.python.org/3.11/library/smtpd.html
.. _pip: https://pip.pypa.io/
.. _Sphinx: https://www.sphinx-doc.org/
.. _tox: https://tox.wiki/
.. _ReadTheDocs: https://bonzo.readthedocs.io
.. _apache-license: http://www.apache.org/licenses/LICENSE-2.0.html
.. |apache-license| replace:: Apache License, Version 2.0
.. _Freakofnurture: http://commons.wikimedia.org/wiki/User:Freakofnurture
.. _image-source: http://commons.wikimedia.org/wiki/File:Zoso_John_Bonham_sigil_three_intersecting_circles.svg
.. |image-source| replace:: source
