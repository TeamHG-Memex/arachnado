# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

from scrapy import signals

from .realtime import BaseWSHandler


logger = logging.getLogger(__name__)


class Monitor(BaseWSHandler):
    """ WebSocket handler which pushes CrawlerProcess events to a client """

    def initialize(self, crawler_process):
        self.crawler_process = crawler_process

    def on_open(self):
        logger.debug("new connection")

    def on_close(self):
        logger.debug("connection closed")
