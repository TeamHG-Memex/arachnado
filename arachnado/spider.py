# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
import logging

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http.response.html import HtmlResponse

from .utils import MB, add_scheme_if_missing, get_netloc
from .crawler_process import ArachnadoCrawler


DEFAULT_SETTINGS = {
    'DEPTH_STATS_VERBOSE': True,
    'DEPTH_PRIORITY': -1,

    'BOT_NAME': 'arachnado',
    'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/39.0.2148.0 Safari/537.36',

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

    'ITEM_PIPELINES': {
        'arachnado.motor_exporter.pipelines.MotorPipeline': 100,
    },

    'MOTOR_PIPELINE_JOBID_KEY': '_job_id',

    'HTTPCACHE_ENABLED': False,
    # This storage is read-only. Responses are stored by MotorPipeline
    'HTTPCACHE_STORAGE': 'arachnado.extensions.httpcache.'
                         'ArachnadoCacheStorage',
}


def create_crawler(settings=None, spider_cls=None):
    _settings = DEFAULT_SETTINGS.copy()
    _settings.update(settings or {})
    return ArachnadoCrawler(spider_cls, _settings)


class ArachnadoSpider(scrapy.Spider):
    """
    A base spider that contains common attributes and utilities for all
    Arachnado spiders
    """
    crawl_id = None
    domain = None
    motor_job_id = None

    def __init__(self, *args, **kwargs):
        super(ArachnadoSpider, self).__init__(*args, **kwargs)
        # don't log scraped items
        logging.getLogger("scrapy.core.scraper").setLevel(logging.INFO)

    def get_page_item(self, response, type_='page'):
        return {
            'crawled_at': datetime.datetime.utcnow(),
            'url': response.url,
            'status': response.status,
            'headers': response.headers,
            'body': response.body_as_unicode(),
            'meta': response.meta,
            '_type': type_,
        }


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

        yield self.get_page_item(response)

        for link in self.get_links(response):
            yield scrapy.Request(link.url, self.parse)
