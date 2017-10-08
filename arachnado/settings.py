# -*- coding: utf-8 -*-
"""
Default settings for Arachnado Scrapy spiders.
"""

DEPTH_STATS_VERBOSE = True
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'
LOG_UNSERIALIZABLE_REQUESTS = True
DISK_QUEUES_ROOT = './.scrapy/jobs'
SCHEDULER = "arachnado.scheduler.scheduler.Scheduler"
REDIS_SCHEDULER_QUEUE_CLASS = "arachnado.scheduler.queue.SpiderPriorityQueue"
DUPEFILTER_CLASS = "arachnado.scheduler.dupefilter.RedisDupeFilter"
# Turn it ON if the goal is to crawl the whole webiste
# (vs crawling most recent content):
PREFER_PAGINATION = False

# To enable autologin turn this option ON and pass AUTOLOGIN_URL
# (e.g. 'http://127.0.0.1:8089')
AUTOLOGIN_ENABLED = False

BOT_NAME = 'arachnado'
COOKIES_DEBUG = False
USER_AGENT = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) '
              'AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/39.0.2148.0 Safari/537.36')

MB = 1024 * 1024
MEMUSAGE_ENABLED = True
DOWNLOAD_MAXSIZE = 1 * MB

# CLOSESPIDER_PAGECOUNT = 30  # for debugging
LOG_LEVEL = 'DEBUG'
TELNETCONSOLE_ENABLED = False

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_DEBUG = False
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DOWNLOAD_DELAY = 0.3  # min download delay
DOWNLOAD_TIMEOUT = 60

STATS_CLASS = 'arachnado.stats.EventedStatsCollector'
DOWNLOADER = 'arachnado.crawler_process.ArachnadoDownloader'

SPIDER_MIDDLEWARES = {
    'arachnado.spidermiddlewares.pageitems.PageItemsMiddleware': 100,
    'arachnado.spidermiddlewares.depth.DepthMiddleware': 150,
    'scrapy.spidermiddlewares.depth.DepthMiddleware': None,
}

DOWNLOADER_MIDDLEWARES = {
    'arachnado.pagecache.httpcache.HttpCacheMiddleware': 230,
    'arachnado.downloadermiddlewares.proxyfromsettings.ProxyFromSettingsMiddleware': 240,
    'arachnado.downloadermiddlewares.droprequests.DropRequestsMiddleware': 250,
    'autologin_middleware.AutologinMiddleware': 605,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
    'autologin_middleware.ExposeCookiesMiddleware': 700,
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': 720,
    'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 730,
}

ITEM_PIPELINES = {
    'arachnado.pipelines.nodupsexport.NoDupsExportPipeline': 10,
    'arachnado.pipelines.esexport.ElasticSearchExportPipeline': 20,
}

EXTENSIONS = {
    'arachnado.extensions.queuesize.QueueSizeExtension': 100,
}

MONGO_EXPORT_ENABLED = True
MONGO_EXPORT_JOBID_KEY = '_job_id'

HTTPCACHE_ENABLED = True
HTTPCACHE_CLEANUP_PARAMS = {}
HTTPCACHE_STORAGE = 'arachnado.pagecache.composite.CompositeCacheStorage'
HTTPCACHE_POLICY = 'arachnado.pagecache.policy.CrawledDatePolicy'
HTTPCACHE_MAX_DAYS_AGE = 15
