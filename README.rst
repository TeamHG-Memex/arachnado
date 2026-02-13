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

Arachnado requires Python 2.7 or Python 3.5.
To install Arachnado use pip::

    pip install arachnado

Run
---

To start Arachnado execute ``arachnado`` command::

    arachnado

and then visit http://0.0.0.0:8888 (or whatever URL is configured).

To see available command-line options use

    arachnado --help

Arachnado can be configured using a config file. Put it to one of the common
locations ('/etc/arachnado.conf', '~/.config/arachnado.conf'
or '~/.arachnado.conf') or pass the file name as an argument when starting
the server::

    arachnado --config ./my-config.conf

For available options check
https://github.com/TeamHG-Memex/arachnado/blob/master/arachnado/config/defaults.conf.

Features
--------

Arachnado provides several features for managing web crawls:

* **Web UI**: Start, stop, pause, and resume crawls through a user-friendly interface
* **HTTP API**: Programmatic access to all crawling functions
* **Custom Spiders**: Upload your own Scrapy projects and run custom spiders
* **Job Management**: Monitor running jobs and view crawl statistics
* **MongoDB Storage**: Store crawled items and job information

Uploading Custom Spiders
~~~~~~~~~~~~~~~~~~~~~~~~~

You can upload your own Scrapy projects via the web UI:

1. Package your Scrapy project as a zip or tar.gz file
2. Use the "Upload Scrapy Project" panel on the main page
3. Enter a project name and select your archive file
4. Click "Upload Project"

Once uploaded, you can run spiders from your project by using the
``spider://<spider_name>`` format in the crawl form.

For more details on the HTTP API for uploading projects, see the documentation.

Tests
-----

To run tests make sure tox_ is installed, then
execute ``tox`` command from the source root.

.. _tox: https://testrun.org/tox/latest/

Development
-----------

* Source code: https://github.com/TeamHG-Memex/arachnado
* Issue tracker: https://github.com/TeamHG-Memex/arachnado/issues

To build Arachnado static assets node.js + npm are required.
Install all JavaScript requirements using npm - run the following command
from the repo root::

    npm install

then rebuild static files (we use Webpack_)::

    npm run build

or auto-build static files on each change during development::

    npm run watch

.. _Webpack: https://github.com/webpack/webpack

----

.. image:: https://hyperiongray.s3.amazonaws.com/define-hg.svg
	:target: https://www.hyperiongray.com/?pk_campaign=github&pk_kwd=arachnado
	:alt: define hyperiongray
