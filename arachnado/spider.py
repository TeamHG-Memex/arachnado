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
    'DEPTH_LIMIT': 10,
    'DEPTH_STATS_VERBOSE': True,
    'BOT_NAME': 'arachnado',

    'MEMUSAGE_ENABLED': True,
    'DOWNLOAD_MAXSIZE': 1 * MB,
    # 'DOWNLOAD_WARNSIZE': 1 * MB,  # see https://github.com/scrapy/scrapy/issues/1303

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
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.5,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
    'DOWNLOAD_DELAY': 0.3,  # min download delay

    'STATS_CLASS': 'arachnado.stats.EventedStatsCollector',
    'DOWNLOADER': 'arachnado.crawler_process.ArachnadoDownloader',

    'DOWNLOAD_HANDLERS': {'s3': None},  # see https://github.com/scrapy/scrapy/issues/1054

    'ITEM_PIPELINES': {
        'arachnado.motor_exporter.pipelines.MotorPipeline': 100,
    },

    'MOTOR_PIPELINE_JOBID_KEY': '_job_id',
}


def create_crawler(settings=None):
    _settings = DEFAULT_SETTINGS.copy()
    _settings.update(settings or {})
    return ArachnadoCrawler(CrawlWebsiteSpider, _settings)


class CrawlWebsiteSpider(scrapy.Spider):
    """
    A spider which crawls all the website.
    To run it, set its ``crawl_id`` and ``domain`` arguments.
    """
    name = 'crawlwebsite'

    crawl_id = None
    domain = None
    motor_job_id = None

    def __init__(self, *args, **kwargs):
        super(CrawlWebsiteSpider, self).__init__(*args, **kwargs)
        self.start_url = add_scheme_if_missing(self.domain)

        # don't log scraped items
        logging.getLogger("scrapy.core.scraper").setLevel(logging.INFO)

    def start_requests(self):
        self.logger.info("Started job %s#%d for domain %s",
                         self.motor_job_id, self.crawl_id, self.domain)
        yield scrapy.Request(self.start_url, self.parse_first, dont_filter=True)

    def parse_first(self, response):
        # If there is a redirect in the first request, use the target domain
        # to restrict crawl instead of the original.
        self.domain = get_netloc(response.url)
        self.crawler.stats.set_value('arachnado/start_url', self.start_url)
        self.crawler.stats.set_value('arachnado/domain', self.domain)

        allow_domain = self.domain
        if self.domain.startswith("www."):
            allow_domain = allow_domain[len("www."):]

        self.get_links = LinkExtractor(allow_domains=[allow_domain]).extract_links
        for elem in self.parse(response):
            yield elem

    def parse(self, response):
        if not isinstance(response, HtmlResponse):
            self.logger.info("non-HTML response is skipped: %s" % response.url)
            return

        yield {
            'crawled_at': datetime.datetime.utcnow(),
            'url': response.url,
            'status': response.status,
            'headers': response.headers,
            'body': response.body_as_unicode(),
            'meta': response.meta,
        }

        for link in self.get_links(response):
            yield scrapy.Request(link.url, self.parse)
