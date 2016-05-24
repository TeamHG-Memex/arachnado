# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import uuid

from arachnado.crawler_process import ArachnadoCrawler
from scrapy.settings import Settings

import arachnado.settings
from arachnado.spider import CrawlWebsiteSpider, ArachnadoSpider
from arachnado.utils.spiders import get_spider_cls


class DomainCrawlers(object):
    """
    Helper class to create and start crawlers.
    """
    def __init__(self, crawler_process, spider_packages, settings):
        self.settings = get_settings(settings)
        self.crawler_process = crawler_process
        self.spider_packages = spider_packages

    def crawl_domain(self, domain, args, settings):
        """ Create, start and return a crawler for a given domain. """
        spider_cls = get_spider_cls(domain, self.spider_packages,
                                    CrawlWebsiteSpider)
        if not spider_cls:
            return

        crawl_id = uuid.uuid4().hex
        crawler = self._create_crawler(crawl_id, spider_cls, settings)
        self.crawler_process.crawl(crawler,
                                   domain=domain,
                                   crawl_id=crawl_id,
                                   **args)
        return crawler

    def _create_crawler(self, crawl_id, spider_cls, settings=None):
        _settings = Settings(self.settings)
        _settings.setdict(settings, 'cmdline')

        root = _settings.get('DISK_QUEUES_ROOT')
        jobdir = os.path.join(root, crawl_id)
        _settings.set('JOBDIR', jobdir, priority='cmdline')

        spider_cls = ArachnadoSpider.inherit_from_me(spider_cls)
        return ArachnadoCrawler(spider_cls, _settings)


def get_settings(overrides=None):
    """
    Return a Settings object, using arachnado.settings as defaults.

    >>> s = get_settings({'DOWNLOAD_DELAY': 100})

    From arachnado.settings.py:

    >>> s['STATS_CLASS']
    'arachnado.stats.EventedStatsCollector'

    Scrapy defaults are preserved:

    >>> s['COMPRESSION_ENABLED']
    True

    Overrides are applied:

    >>> s['DOWNLOAD_DELAY']
    100
    """
    settings = Settings()
    settings.setmodule(arachnado.settings)
    settings.setdict(overrides, 'spider')
    return settings
