Development Guide
==================

This guide explains how to set up a development environment for Arachnado,
build the project from source, run tests, and create custom extensions.

Building From Source
--------------------

Prerequisites
~~~~~~~~~~~~~

Arachnado requires:

* Python 2.7 or Python 3.5+
* Node.js and npm (for building frontend assets)
* MongoDB (optional, for data storage)

Setting Up Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Clone the repository::

    git clone https://github.com/TeamHG-Memex/arachnado.git
    cd arachnado

2. Create and activate a virtual environment (recommended)::

    # Using virtualenv
    virtualenv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Or using Python 3's venv
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install Python dependencies::

    pip install -r requirements.txt

4. Install the package in development mode::

    pip install -e .

   This will install Arachnado in "editable" mode, so changes to the code
   will be immediately reflected without reinstalling.

Building Frontend Assets
~~~~~~~~~~~~~~~~~~~~~~~~~

Arachnado uses React for the frontend and Webpack for bundling JavaScript assets.

1. Install JavaScript dependencies::

    npm install

2. Build the frontend assets::

    # Production build (minified)
    npm run build

    # Development build with file watching (auto-rebuild on changes)
    npm run watch

The built assets will be placed in ``arachnado/static/build/``.

Running Arachnado
~~~~~~~~~~~~~~~~~

After building from source, you can run Arachnado::

    arachnado

Then visit http://0.0.0.0:8888 to see the web interface.

For development with custom configuration, you can create a config file::

    arachnado --config ./my-dev-config.conf

See :ref:`config` for available configuration options.

Running Tests
-------------

Arachnado uses tox for running tests across multiple Python versions.

Running All Tests
~~~~~~~~~~~~~~~~~

To run the full test suite::

    tox

This will run tests for Python 2.7 and Python 3.5.

Running Tests for a Specific Python Version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To run tests for a specific Python version::

    tox -e py27  # For Python 2.7
    tox -e py35  # For Python 3.5

Running Tests Directly with pytest
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to run tests without tox::

    pip install pytest pytest-cov
    py.test --doctest-modules --cov=arachnado arachnado tests

Running Specific Tests
~~~~~~~~~~~~~~~~~~~~~~

To run specific test files or test functions::

    py.test tests/test_data.py
    py.test tests/test_data.py::test_function_name

Creating Extensions
-------------------

Arachnado is built on top of Scrapy, so you can create custom Scrapy extensions
to add functionality to the crawler.

Extension Structure
~~~~~~~~~~~~~~~~~~~

An extension is a Python class that implements specific methods and hooks into
Scrapy signals. Here's the basic structure::

    from scrapy import signals

    class MyCustomExtension(object):
        """
        Description of what your extension does.
        """
        def __init__(self, crawler):
            self.crawler = crawler
            # Connect to signals
            crawler.signals.connect(self.spider_opened,
                                    signal=signals.spider_opened)
            crawler.signals.connect(self.spider_closed,
                                    signal=signals.spider_closed)

        @classmethod
        def from_crawler(cls, crawler):
            """Required method to initialize the extension."""
            return cls(crawler)

        def spider_opened(self, spider):
            """Called when a spider is opened."""
            # Your code here
            pass

        def spider_closed(self, spider):
            """Called when a spider is closed."""
            # Your code here
            pass

Example: Queue Size Extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's a real example from Arachnado that tracks queue size::

    from scrapy import signals

    class QueueSizeExtension(object):
        """
        This extension adds two fields to scrapy stats:

        * 'scheduler/initial' with an initial number of requests when
          spider starts;
        * 'scheduler/remaining' with a remaining number of requests when
          spider stops.
        """
        def __init__(self, crawler):
            crawler.signals.connect(self.spider_opened,
                                    signal=signals.spider_opened)
            crawler.signals.connect(self.spider_closed,
                                    signal=signals.spider_closed)
            self.crawler = crawler

        @classmethod
        def from_crawler(cls, crawler):
            return cls(crawler)

        def spider_opened(self, spider):
            self.crawler.stats.set_value('scheduler/initial',
                                         self._num_requests())

        def spider_closed(self, spider):
            self.crawler.stats.set_value('scheduler/remaining',
                                         self._num_requests())

        def _num_requests(self):
            scheduler = self.crawler.engine.slot.scheduler
            return len(scheduler)

Registering Extensions
~~~~~~~~~~~~~~~~~~~~~~

To use your extension, add it to the ``EXTENSIONS`` setting in your
configuration or in ``arachnado/settings.py``::

    EXTENSIONS = {
        'myproject.extensions.MyCustomExtension': 100,
    }

The number (100) is the order in which the extension will be loaded.
Lower numbers are loaded first.

Available Signals
~~~~~~~~~~~~~~~~~

Common Scrapy signals you can hook into:

* ``signals.spider_opened`` - When a spider is opened
* ``signals.spider_closed`` - When a spider is closed
* ``signals.spider_idle`` - When a spider becomes idle
* ``signals.request_scheduled`` - When a request is scheduled
* ``signals.request_dropped`` - When a request is dropped
* ``signals.response_received`` - When a response is received
* ``signals.response_downloaded`` - When a response is downloaded
* ``signals.item_scraped`` - When an item is scraped
* ``signals.item_dropped`` - When an item is dropped

See `Scrapy Signals documentation <https://docs.scrapy.org/en/latest/topics/signals.html>`_
for a complete list.

Creating Pipelines
------------------

Item pipelines are used to process items after they are extracted from pages.
Common uses include data cleaning, validation, and storage.

Pipeline Structure
~~~~~~~~~~~~~~~~~~

A pipeline is a Python class with a ``process_item`` method::

    from scrapy.exceptions import DropItem

    class MyCustomPipeline(object):
        """
        Description of what your pipeline does.
        """
        def __init__(self, crawler):
            self.crawler = crawler
            # Initialize your pipeline
            pass

        @classmethod
        def from_crawler(cls, crawler):
            """Optional: Initialize pipeline with crawler settings."""
            return cls(crawler)

        def open_spider(self, spider):
            """Optional: Called when spider is opened."""
            pass

        def close_spider(self, spider):
            """Optional: Called when spider is closed."""
            pass

        def process_item(self, item, spider):
            """
            Process an item. This method must:
            - return the item
            - return a Deferred
            - or raise DropItem exception
            """
            # Process your item here
            # item['processed_field'] = process(item['field'])
            
            # Optionally drop items
            # if not self.is_valid(item):
            #     raise DropItem("Invalid item")
            
            return item

Async Pipeline Example
~~~~~~~~~~~~~~~~~~~~~~

For I/O operations like database writes, use async pipelines with Tornado::

    from tornado import gen
    from arachnado.utils.twistedtornado import tt_coroutine

    class AsyncStoragePipeline(object):
        """
        Store items asynchronously.
        """
        @classmethod
        def from_crawler(cls, crawler):
            return cls(crawler)

        def __init__(self, crawler):
            self.crawler = crawler

        @tt_coroutine
        def open_spider(self, spider):
            # Setup async resources
            pass

        @tt_coroutine
        def process_item(self, item, spider):
            # Async processing
            # yield some_async_operation(item)
            raise gen.Return(item)

        @tt_coroutine
        def close_spider(self, spider):
            # Cleanup async resources
            pass

Registering Pipelines
~~~~~~~~~~~~~~~~~~~~~

Add your pipeline to ``ITEM_PIPELINES`` in settings::

    ITEM_PIPELINES = {
        'myproject.pipelines.MyCustomPipeline': 100,
    }

Lower numbers run first. Standard range is 0-1000.

Creating Middlewares
--------------------

Middlewares can be used to process requests and responses at different stages.

Spider Middleware
~~~~~~~~~~~~~~~~~

Spider middlewares process spider input (responses) and output (items and requests)::

    class MySpiderMiddleware(object):
        def process_spider_input(self, response, spider):
            """
            Called for each response that goes through the spider
            middleware and into the spider.
            """
            return None

        def process_spider_output(self, response, result, spider):
            """
            Called with the results returned from the Spider, after
            it has processed the response.
            """
            for item in result:
                yield item

        def process_spider_exception(self, response, exception, spider):
            """
            Called when a spider or process_spider_input() method
            raises an exception.
            """
            pass

Downloader Middleware
~~~~~~~~~~~~~~~~~~~~~

Downloader middlewares process requests before they are sent and responses
before they reach the spider::

    class MyDownloaderMiddleware(object):
        def process_request(self, request, spider):
            """
            Called for each request that goes through the downloader
            middleware.
            
            Must return: None, a Response, a Request, or raise IgnoreRequest
            """
            return None

        def process_response(self, request, response, spider):
            """
            Called with the response returned from the downloader.
            
            Must return: a Response, a Request, or raise IgnoreRequest
            """
            return response

        def process_exception(self, request, exception, spider):
            """
            Called when a download handler or a process_request()
            raises an exception.
            """
            pass

Registering Middlewares
~~~~~~~~~~~~~~~~~~~~~~~

Add spider middlewares to ``SPIDER_MIDDLEWARES``::

    SPIDER_MIDDLEWARES = {
        'myproject.middlewares.MySpiderMiddleware': 100,
    }

Add downloader middlewares to ``DOWNLOADER_MIDDLEWARES``::

    DOWNLOADER_MIDDLEWARES = {
        'myproject.middlewares.MyDownloaderMiddleware': 100,
    }

Best Practices
--------------

Code Organization
~~~~~~~~~~~~~~~~~

When developing extensions for Arachnado:

* Place extensions in ``arachnado/extensions/``
* Place pipelines in ``arachnado/pipelines/``
* Place middlewares in ``arachnado/spidermiddlewares/`` or ``arachnado/downloadermiddlewares/``
* Add tests in the ``tests/`` directory
* Document your extensions with docstrings

Configuration
~~~~~~~~~~~~~

* Use Scrapy settings for configuration options
* Access settings via ``crawler.settings.get()`` or ``crawler.settings.getbool()``
* Provide sensible defaults
* Document all configuration options

Logging
~~~~~~~

Use Python's logging module::

    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Info message", extra={'crawler': self.crawler})
    logger.error("Error message", exc_info=True, extra={'crawler': self.crawler})

Testing
~~~~~~~

* Write unit tests for your extensions
* Test with different configurations
* Mock external dependencies
* Use pytest fixtures for common setup

Contributing
------------

If you've created a useful extension and want to contribute it back to Arachnado:

1. Fork the repository on GitHub
2. Create a feature branch from master
3. Make your changes with tests and documentation
4. Ensure all tests pass with ``tox``
5. Submit a pull request

See the `GitHub repository <https://github.com/TeamHG-Memex/arachnado>`_ for more information.

Additional Resources
--------------------

* `Scrapy Documentation <https://docs.scrapy.org/>`_ - Core framework documentation
* `Tornado Documentation <http://www.tornadoweb.org/>`_ - Async web framework
* `React Documentation <https://reactjs.org/>`_ - Frontend framework
* `Webpack Documentation <https://webpack.js.org/>`_ - Asset bundling

For questions or issues, please visit the
`issue tracker <https://github.com/TeamHG-Memex/arachnado/issues>`_.
