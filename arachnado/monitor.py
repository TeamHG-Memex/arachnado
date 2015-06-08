# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

from scrapy import signals
from .crawler_process import ArachnadoCrawlerProcess
from .realtime import BaseWSHandler
from .cpsignals import CrawlerProcessSignals

logger = logging.getLogger(__name__)


class Monitor(BaseWSHandler):
    """ WebSocket handler which pushes CrawlerProcess events to a client """

    def initialize(self, crawler_process):
        """
        :param ArachnadoCrawlerProcess crawler_process: crawler process
        """
        self.cp = crawler_process
        self.cp.signals.connect(self.on_spider_opened, CrawlerProcessSignals.spider_opened)
        self.cp.signals.connect(self.on_spider_closed, CrawlerProcessSignals.spider_closed)

    def on_open(self):
        logger.debug("new connection")
        self.write_event("jobs:state", self.cp.jobs)

    def on_close(self):
        logger.debug("connection closed")

    def on_spider_opened(self, spider):
        logger.debug("on_spider_opened: %s", self.cp.jobs)
        self.write_event("jobs:state", self.cp.jobs)

    def on_spider_closed(self, spider, reason):
        logger.debug("on_spider_closed: %s", self.cp.jobs)
        self.write_event("jobs:state", self.cp.jobs)

