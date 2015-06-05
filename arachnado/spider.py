# -*- coding: utf-8 -*-
from __future__ import absolute_import
import scrapy
from scrapy.crawler import Crawler
from scrapy.linkextractors import LinkExtractor

MB = 1024*1024

DEFAULT_SETTINGS = {
    # 'DEPTH_LIMIT': 1,
    # 'DEPTH_STATS_VERBOSE': True,

    'DOWNLOAD_MAXSIZE': 8 * MB,
    'DOWNLOAD_WARNSIZE': 1 * MB,
    # 'DOWNLOAD_DELAY': 3,
    'CLOSESPIDER_PAGECOUNT': 3,  # for debugging
    'LOG_LEVEL': 'DEBUG',
    'TELNETCONSOLE_ENABLED': False,

    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_DEBUG': False,
    'AUTOTHROTTLE_START_DELAY': 3,
}


def get_crawler(settings=None):
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
        self.get_links = LinkExtractor(allow_domains=[self.domain]).extract_links

    def start_requests(self):
        self.logger.info("Started job #%d for domain %s", self.crawl_id, self.domain)
        yield scrapy.Request("http://%s" % self.domain, self.parse)

    def parse(self, response):
        yield {'_url': response.url, '_crawl_id': self.crawl_id}

        for link in self.get_links(response):
            yield scrapy.Request(link.url, self.parse)
