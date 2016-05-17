# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http.response.html import HtmlResponse

from arachnado.utils.misc import MB, add_scheme_if_missing, get_netloc


DEFAULT_SETTINGS = {
    'DEPTH_STATS_VERBOSE': True,
    'DEPTH_PRIORITY': -1,

    'BOT_NAME': 'arachnado',
    'COOKIES_DEBUG': False,

    'MEMUSAGE_ENABLED': True,
    'DOWNLOAD_MAXSIZE': 1 * MB,
    # see https://github.com/scrapy/scrapy/issues/1303
    # 'DOWNLOAD_WARNSIZE': 1 * MB,

    # 'CLOSESPIDER_PAGECOUNT': 30,  # for debugging
    'LOG_LEVEL': 'DEBUG',
    'TELNETCONSOLE_ENABLED': False,
    # 'CONCURRENT_REQUESTS': 100,

    'EXTENSIONS': {
        'scrapy.extensions.throttle.AutoThrottle': None,
        'arachnado.extensions.throttle.AutoThrottle': 0,
    },

    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_DEBUG': False,
    'AUTOTHROTTLE_START_DELAY': 5,
    'AUTOTHROTTLE_MAX_DELAY': 60,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
    'DOWNLOAD_DELAY': 0.3,  # min download delay

    'STATS_CLASS': 'arachnado.stats.EventedStatsCollector',
    'DOWNLOADER': 'arachnado.crawler_process.ArachnadoDownloader',

    # see https://github.com/scrapy/scrapy/issues/1054
    'DOWNLOAD_HANDLERS': {'s3': None},

    'SPIDER_MIDDLEWARES': {
        'arachnado.spidermiddlewares.pageitems.PageItemsMiddleware': 100,
    },
    'DOWNLOADER_MIDDLEWARES': {
        'arachnado.downloadermiddlewares.proxyfromsettings'
        '.ProxyFromSettingsMiddleware': 10,
    },
    'ITEM_PIPELINES': {
        'arachnado.pipelines.mongoexport.MongoExportPipeline': 10,
    },
    'MONGO_EXPORT_ENABLED': True,
    'MONGO_EXPORT_JOBID_KEY': '_job_id',
    'HTTPCACHE_ENABLED': False,
    # This storage is read-only. Responses are stored by PageExport middleware
    'HTTPCACHE_STORAGE': 'arachnado.pagecache.mongo.MongoCacheStorage',
}


class ArachnadoSpider(scrapy.Spider):
    """
    A base spider that contains common attributes and utilities for all
    Arachnado spiders
    """
    crawl_id = None
    domain = None
    motor_job_id = None
    kwargs = None
    user_settings = None
    flags = None

    def __init__(self, *args, **kwargs):
        super(ArachnadoSpider, self).__init__(*args, **kwargs)

        self.flags = set()
        self.kwargs = kwargs
        # don't log scraped items
        logging.getLogger("scrapy.core.scraper").setLevel(logging.INFO)


class CrawlWebsiteSpider(ArachnadoSpider):
    """
    A spider which crawls all the website.
    To run it, set its ``crawl_id`` and ``domain`` arguments.
    """
    name = 'crawlwebsite'
    custom_settings = {
        'DEPTH_LIMIT': 10,
    }

    def __init__(self, *args, **kwargs):
        super(CrawlWebsiteSpider, self).__init__(*args, **kwargs)
        self.start_url = add_scheme_if_missing(self.domain)

    def start_requests(self):
        self.logger.info("Started job %s#%d for domain %s",
                         self.motor_job_id, self.crawl_id, self.domain)
        yield scrapy.Request(self.start_url, self.parse_first,
                             dont_filter=True)

    def parse_first(self, response):
        # If there is a redirect in the first request, use the target domain
        # to restrict crawl instead of the original.
        self.domain = get_netloc(response.url)
        self.crawler.stats.set_value('arachnado/start_url', self.start_url)
        self.crawler.stats.set_value('arachnado/domain', self.domain)

        allow_domain = self.domain
        if self.domain.startswith("www."):
            allow_domain = allow_domain[len("www."):]
        self.get_links = LinkExtractor(
            allow_domains=[allow_domain]
        ).extract_links

        for elem in self.parse(response):
            yield elem

    def parse(self, response):
        if not isinstance(response, HtmlResponse):
            self.logger.info("non-HTML response is skipped: %s" % response.url)
            return
        for link in self.get_links(response):
            yield scrapy.Request(link.url, self.parse)
