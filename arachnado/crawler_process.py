# -*- coding: utf-8 -*-
from __future__ import absolute_import
from tornado.platform.twisted import TwistedIOLoop
from scrapy.crawler import CrawlerProcess


class TornadoCrawlerProcess(CrawlerProcess):
    """
    CrawlerProcess which sets up Tornado reactor as well as Twisted,
    and workarounds some Scrapy issues.
    """
    def __init__(self, settings=None):
        TwistedIOLoop().install()
        super(TornadoCrawlerProcess, self).__init__(settings or {})

    def crawl(self, crawler_or_spidercls, *args, **kwargs):
        return super(TornadoCrawlerProcess, self).crawl(crawler_or_spidercls, *args, **kwargs)

    def stop(self):
        # a workaround for https://github.com/scrapy/scrapy/issues/1279
        d = super(TornadoCrawlerProcess, self).stop()
        d.addBoth(self._stop_reactor)
        return d
