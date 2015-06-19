Arachnado
=========

Arachnado is a tool to crawl a specific website.
It provides a Tornado_-based HTTP API and a web UI for a Scrapy_-based
crawler.

License is MIT.

.. _Tornado: http://www.tornadoweb.org
.. _Scrapy: http://scrapy.org/

Install
-------

Python 2.7 is required to run server.
To build static assets node.js + npm are required.

Install all Python requirements from `requirements.txt` using pip::

    pip install -U -r requirements.txt

Install all JavaScript requirements using npm. Run the following command
from the repo root::

    npm install

then rebuild static files (we use Webpack_)::

    npm run build

or auto-build static files on each change during development::

    npm run watch

.. _Webpack: https://github.com/webpack/webpack

Run
---

To run Arachnado execute the following command from the repo root::

    python -m arachnado

Then visit http://127.0.0.1:8888/
