.. _custom-spiders:

Custom Spiders
==============

Arachnado supports running custom Scrapy spiders in addition to its built-in
generic spider. This allows you to create specialized crawlers with custom
logic for specific websites or use cases.

How It Works
------------

By default, Arachnado uses the ``generic`` spider (``CrawlWebsiteSpider``)
which crawls entire websites following links. However, you can create your
own Scrapy spiders and configure Arachnado to use them.

Creating a Custom Spider
-------------------------

1. Create a Python package with your spiders. For example::

    myspiders/
        __init__.py
        spiders/
            __init__.py
            myspider.py

2. Write your spider in ``myspider.py``::

    import scrapy

    class MyCustomSpider(scrapy.Spider):
        name = 'mycustom'

        def start_requests(self):
            # You can access self.domain which is set by Arachnado
            url = getattr(self, 'domain', 'http://example.com')
            yield scrapy.Request(url, self.parse)

        def parse(self, response):
            # Your custom parsing logic
            yield {
                'url': response.url,
                'title': response.css('title::text').get(),
            }

**Important**: Your spider will receive the ``domain`` attribute from Arachnado,
which contains the URL to crawl. You can also access ``crawl_id`` and
``motor_job_id`` attributes.

Configuring Arachnado
---------------------

To use custom spiders, you need to configure Arachnado to load them:

1. Create or edit your Arachnado config file (e.g., ``~/.arachnado.conf``)::

    [arachnado.scrapy]
    spider_packages = myspiders.spiders

You can specify multiple packages separated by whitespace::

    [arachnado.scrapy]
    spider_packages = myspiders.spiders otherpackage.spiders

2. Make sure your spider package is in Python's path. You can:

   * Install it with pip: ``pip install -e /path/to/myspiders``
   * Add it to PYTHONPATH: ``export PYTHONPATH=/path/to/myspiders:$PYTHONPATH``
   * When using Docker, mount your package in ``/python-packages`` volume

Using Custom Spiders
---------------------

There are several ways to use your custom spider:

Via Web UI
~~~~~~~~~~

In the Arachnado web interface, when starting a crawl, use the special
``spider://`` URL format::

    spider://mycustom

This tells Arachnado to use the spider named ``mycustom`` instead of the
default generic spider.

Via API
~~~~~~~

When using the HTTP or WebSocket API, pass the spider URL::

    POST /crawler/start
    {
        "domain": "spider://mycustom",
        "args": {},
        "settings": {}
    }

Via Scheduled Crawls
~~~~~~~~~~~~~~~~~~~~

When creating a scheduled crawl in the database, set the ``engine`` field
to your spider name::

    {
        "url": "http://example.com",
        "engine": "mycustom",
        "schedule": "0 0 * * *"
    }

Inheriting from ArachnadoSpider
--------------------------------

For better integration with Arachnado features, your spider should inherit
from ``ArachnadoSpider``::

    from arachnado.spider import ArachnadoSpider

    class MyCustomSpider(ArachnadoSpider):
        name = 'mycustom'

        def start_requests(self):
            url = self.domain
            yield scrapy.Request(url, self.parse)

        def parse(self, response):
            yield {'url': response.url}

This provides access to:

* ``crawl_id`` - Unique identifier for this crawl job
* ``motor_job_id`` - MongoDB record ID for this job
* ``domain`` - The domain/URL to crawl
* Better logging configuration

Setting a Default Spider
-------------------------

You can change the default spider used when no ``spider://`` URL is provided::

    [arachnado.scrapy]
    spider_packages = myspiders.spiders
    default_spider_name = mycustom

Now all crawls will use ``mycustom`` unless explicitly specified otherwise.

Docker Setup
------------

When using Docker, mount your spider package as a volume::

    docker run -v /path/to/myspiders:/python-packages/myspiders \
               -v /path/to/config.conf:/etc/arachnado.conf \
               arachnado

The ``/python-packages`` directory is automatically added to PYTHONPATH.

Example: Custom Spider with Arguments
--------------------------------------

Your spider can accept custom arguments through the Arachnado UI or API::

    from arachnado.spider import ArachnadoSpider

    class MySpider(ArachnadoSpider):
        name = 'myspider'

        def __init__(self, max_pages=10, *args, **kwargs):
            super(MySpider, self).__init__(*args, **kwargs)
            self.max_pages = int(max_pages)
            self.page_count = 0

        def parse(self, response):
            if self.page_count >= self.max_pages:
                return
            self.page_count += 1
            # ... your parsing logic

Pass arguments via the API::

    {
        "domain": "spider://myspider",
        "args": {"max_pages": "20"},
        "settings": {}
    }

Troubleshooting
---------------

Spider not found
~~~~~~~~~~~~~~~~

If you get an error that your spider cannot be found:

1. Verify the spider name matches the ``name`` attribute in your spider class
2. Check that ``spider_packages`` is correctly configured
3. Ensure your package is in Python's path
4. Restart Arachnado after configuration changes

Spider not receiving domain
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure your spider accepts the ``domain`` parameter in ``__init__``::

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        # domain is available as self.domain

Or access it directly in your spider methods as it's set as an attribute.
