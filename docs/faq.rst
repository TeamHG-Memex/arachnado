Frequently Asked Questions (FAQ)
=================================

Architecture and Design
-----------------------

Why does Arachnado use custom signals and subclass Scrapy's ExecutionEngine and Downloader?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Arachnado extends Scrapy's signal system to provide real-time monitoring and control capabilities that are essential for its web UI and API. The custom signals include:

**Custom Signals Added:**

* ``spider_closing`` - Fires when a spider is scheduled to stop (before ``spider_closed``)
* ``engine_paused`` - Fires when the execution engine is paused
* ``engine_resumed`` - Fires when the execution engine resumes
* ``engine_tick`` - Fires periodically during crawling (throttled to avoid excessive signaling)
* ``downloader_enqueued`` - Fires when a request is enqueued in the downloader
* ``downloader_dequeued`` - Fires when a request is dequeued from the downloader

**Why These Are Needed:**

1. **Real-time UI Updates**: The web interface needs to display live statistics, queue sizes, and crawling status. Standard Scrapy signals don't provide enough granularity for smooth real-time updates.

2. **Pause/Resume Functionality**: Arachnado allows users to pause and resume crawls through the UI. This requires custom signals to notify all connected clients when the engine state changes.

3. **Downloader Queue Monitoring**: The custom downloader signals enable real-time monitoring of the request queue, which is displayed in the web UI to help users understand what's being crawled.

4. **Signal Aggregation**: Arachnado runs multiple crawlers simultaneously. The ``ArachnadoCrawlerProcess`` aggregates signals from all active crawlers and broadcasts them to connected WebSocket clients, requiring a unified signal handling system.

**Implementation Details:**

The ``ArachnadoExecutionEngine`` extends Scrapy's ``ExecutionEngine`` to:

* Send ``spider_closing`` signal before shutting down
* Send ``engine_paused`` and ``engine_resumed`` signals
* Send throttled ``engine_tick`` signals to avoid overwhelming clients

The ``ArachnadoDownloader`` extends Scrapy's ``Downloader`` to:

* Send ``downloader_enqueued`` and ``downloader_dequeued`` signals for queue monitoring

Why does Arachnado use WebSockets instead of just HTTP API?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Arachnado uses **both** WebSockets and HTTP API, each serving different purposes:

**HTTP API** (documented in :doc:`http-api`):

* Used for starting, stopping, pausing, and resuming crawls
* Simple request/response operations
* REST-style interface for crawler control

**WebSocket API** (documented in :doc:`json-rpc-api`):

* Used for **real-time streaming** of crawl data and statistics
* Provides live updates to the web UI without polling
* Enables efficient subscription-based data delivery

**Why WebSockets Are Essential:**

1. **Real-time Updates**: The web UI displays live statistics (pages crawled, items scraped, queue sizes, etc.). WebSockets allow the server to push updates instantly without the client polling repeatedly.

2. **Efficient Data Streaming**: When crawling thousands of pages, WebSockets efficiently stream results to clients as they're discovered, rather than requiring clients to repeatedly query for new data.

3. **Bidirectional Communication**: Clients can subscribe to specific data streams (e.g., "show me all pages from example.com") and receive only relevant updates.

4. **Reduced Server Load**: WebSocket subscriptions eliminate the need for frequent HTTP polling, significantly reducing server load and network traffic.

5. **Live Monitoring**: Multiple users can monitor ongoing crawls in real-time through the web UI, with instant updates when crawl state changes.

**When to Use Each:**

* Use **HTTP API** to start/stop/pause/resume crawls programmatically
* Use **WebSocket API** to subscribe to real-time crawl data and statistics
* The web UI uses both: HTTP API for controls, WebSockets for live updates

Does Arachnado obey regular Scrapy middleware (cookies, robots.txt, etc.)?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Yes**, Arachnado is built on top of Scrapy and **fully supports standard Scrapy middleware**, including:

* **CookiesMiddleware**: Cookie handling works normally (note: Arachnado uses ``autologin-middleware.ExposeCookiesMiddleware`` by default, which extends cookie functionality)
* **RobotsTxtMiddleware**: Robots.txt rules are obeyed by default (can be disabled via Scrapy settings)
* **UserAgentMiddleware**: User-Agent headers work as expected
* **RetryMiddleware**: Request retries work normally
* **RedirectMiddleware**: HTTP redirects are handled properly
* **HttpCompressionMiddleware**: Compression is supported
* **All other standard Scrapy middleware**: Works as documented in Scrapy

**Custom Middleware in Arachnado:**

Arachnado adds some custom middleware (see ``arachnado/settings.py``):

* ``ProxyFromSettingsMiddleware`` - Allows setting proxies via settings
* ``DropRequestsMiddleware`` - Can drop requests based on conditions
* ``AutologinMiddleware`` - Provides automatic login functionality (when enabled)
* ``ExposeCookiesMiddleware`` - Makes cookies accessible in items
* ``PageItemsMiddleware`` - Processes scraped items for export

**Important Note on CookiesMiddleware:**

The default settings disable Scrapy's standard ``CookiesMiddleware`` and use ``ExposeCookiesMiddleware`` instead (priority 700). This is done to make cookies accessible in scraped items while maintaining full cookie functionality.

**Configuring Middleware:**

You can configure any standard Scrapy middleware through:

1. The configuration file (see :doc:`config`)
2. The ``settings`` parameter when starting a crawl
3. Spider-level settings

Example starting a crawl with custom middleware settings::

    POST /crawler/start
    {
        "domain": "example.com",
        "settings": {
            "ROBOTSTXT_OBEY": false,
            "COOKIES_ENABLED": true
        }
    }

Does Arachnado use Splash as a browser?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Arachnado supports Splash but doesn't require it.**

**Splash Support:**

* Arachnado includes code to handle Splash requests (see ``arachnado/crawler_process.py``::_request_info method)
* If your spider uses Splash (via ``scrapy-splash``), Arachnado will properly display Splash requests in the UI
* The downloader statistics extraction recognizes Splash metadata and displays the actual URL being rendered

**Using Splash with Arachnado:**

To use Splash with Arachnado:

1. Install ``scrapy-splash``::

    pip install scrapy-splash

2. Configure Splash settings when starting a crawl::

    POST /crawler/start
    {
        "domain": "example.com",
        "settings": {
            "SPLASH_URL": "http://localhost:8050",
            "DOWNLOADER_MIDDLEWARES": {
                "scrapy_splash.SplashCookiesMiddleware": 723,
                "scrapy_splash.SplashMiddleware": 725,
                "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810
            },
            "SPIDER_MIDDLEWARES": {
                "scrapy_splash.SplashDeduplicateArgsMiddleware": 100
            },
            "DUPEFILTER_CLASS": "scrapy_splash.SplashAwareDupeFilter"
        }
    }

3. Use Splash requests in your spider code following ``scrapy-splash`` documentation

**Without Splash:**

By default, Arachnado uses standard Scrapy HTTP downloads without JavaScript rendering. This is suitable for most websites that don't heavily rely on JavaScript.

Do autologin and FormRequest work with Arachnado?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Yes, both are supported.**

**Autologin Support:**

Arachnado includes built-in support for automatic login via the ``autologin-middleware`` package (see :doc:`config`):

1. **Enable autologin** in your configuration::

    AUTOLOGIN_ENABLED = True
    AUTOLOGIN_URL = 'http://127.0.0.1:8089'

2. The ``autologin-middleware`` will automatically:
   - Detect login forms
   - Use the autologin service to fill in credentials
   - Handle authentication automatically

3. **Autologin middleware is already configured** in Arachnado's default settings (priority 605)

**FormRequest Support:**

Standard Scrapy ``FormRequest`` works normally with Arachnado:

1. **Use in your spider** as documented in Scrapy::

    from scrapy.http import FormRequest

    def parse(self, response):
        return FormRequest.from_response(
            response,
            formdata={'username': 'admin', 'password': 'secret'},
            callback=self.after_login
        )

2. **FormRequest features fully supported**:
   - ``FormRequest.from_response()`` for form parsing
   - Custom form data
   - File uploads
   - All standard FormRequest functionality

**Example - Starting a Crawl with Autologin:**

Via HTTP API::

    POST /crawler/start
    {
        "domain": "https://example.com/login",
        "settings": {
            "AUTOLOGIN_ENABLED": true,
            "AUTOLOGIN_URL": "http://localhost:8089"
        }
    }

**Note on Cookies:**

Both autologin and FormRequest rely on cookie handling, which is fully supported in Arachnado through the ``ExposeCookiesMiddleware`` (configured by default).

Related Documentation
---------------------

* :doc:`intro` - Getting started with Arachnado
* :doc:`http-api` - HTTP API documentation
* :doc:`json-rpc-api` - WebSocket JSON-RPC API documentation
* :doc:`config` - Configuration options

External Resources
------------------

* `Scrapy Documentation <https://doc.scrapy.org/>`_ - For standard Scrapy features
* `scrapy-splash Documentation <https://github.com/scrapy-plugins/scrapy-splash>`_ - For JavaScript rendering
* `autologin-middleware Documentation <https://github.com/TeamHG-Memex/autologin-middleware>`_ - For automatic login
