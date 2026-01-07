# -*- coding: utf-8 -*-
from __future__ import absolute_import  
from scrapy import signals


class QueueSizeExtension(object):
    """
    This extension adds two fields to scrapy stats:

    * 'scheduler/initial' with an initial number of requests when
      spider strats;
    * 'scheduler/remaining' with a remaining number of requests when
      spider stops.

    """
    def __init__(self, crawler):
        crawler.signals.connect(self.spider_opened,
                                signal=signals.spider_opened)
        crawler.signals.connect(self.spider_closed,
                                signal=signals.spider_closed)
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def spider_opened(self, spider):
        self.crawler.stats.set_value('scheduler/initial',
                                     self._num_requests())

    def spider_closed(self, spider):
        self.crawler.stats.set_value('scheduler/remaining',
                                     self._num_requests())

    def _num_requests(self):
        scheduler = self.crawler.engine.slot.scheduler
        return len(scheduler)
