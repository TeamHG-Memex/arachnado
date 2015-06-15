# -*- coding: utf-8 -*-
from __future__ import absolute_import

import scrapy
from scrapy.crawler import Crawler
from scrapy.linkextractors import LinkExtractor

from .utils import MB, add_scheme_if_missing, get_netloc


DEFAULT_SETTINGS = {
    # 'DEPTH_LIMIT': 1,
    # 'DEPTH_STATS_VERBOSE': True,
    'BOT_NAME': 'arachnado',

    'MEMUSAGE_ENABLED': True,
    'DOWNLOAD_MAXSIZE': 1 * MB,
    # 'DOWNLOAD_WARNSIZE': 1 * MB,  # see https://github.com/scrapy/scrapy/issues/1303

    'CLOSESPIDER_PAGECOUNT': 30,  # for debugging
    'LOG_LEVEL': 'DEBUG',
    'TELNETCONSOLE_ENABLED': False,

    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_DEBUG': False,
    'AUTOTHROTTLE_START_DELAY': 3,

    'STATS_CLASS': 'arachnado.stats.EventedStatsCollector',
    'DOWNLOAD_HANDLERS': {'s3': None},  # see https://github.com/scrapy/scrapy/issues/1054
}


def create_crawler(settings=None):
    _settings = DEFAULT_SETTINGS.copy()
    _settings.update(settings or {})
    return Crawler(CrawlWebsiteSpider, _settings)


class CrawlWebsiteSpider(scrapy.Spider):
    """
    A spider which crawls all the website.
    To run it, set its ``crawl_id`` and ``domain`` arguments.
    """
    name = 'crawlwebsite'

    crawl_id = None
    domain = None

    def __init__(self, *args, **kwargs):
        super(CrawlWebsiteSpider, self).__init__(*args, **kwargs)
        self.start_url = add_scheme_if_missing(self.domain)
        self.get_links = LinkExtractor(
            allow_domains=[get_netloc(self.start_url)]
        ).extract_links

    def start_requests(self):
        self.logger.info("Started job #%d for domain %s", self.crawl_id, self.domain)
        yield scrapy.Request(self.start_url, self.parse, dont_filter=True)

    # def get_links(self, response):
    #     from scrapy.link import Link
    #     for href in response.xpath("//a/@href").extract():
    #         url = response.urljoin(href)
    #         yield Link(url.encode('utf8'))

    def parse(self, response):
        yield {'_url': response.url, '_crawl_id': self.crawl_id}

        for link in self.get_links(response):
            yield scrapy.Request(link.url, self.parse)
