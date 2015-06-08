# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import itertools

from scrapy import signals
from scrapy.signalmanager import SignalManager
from scrapy.crawler import CrawlerProcess, Crawler

from .cpsignals import CrawlerProcessSignals, SIGNAL_NAMES

logger = logging.getLogger(__name__)


class ArachnadoCrawlerProcess(CrawlerProcess):
    """
    CrawlerProcess which sets up a global signals manager,
    assigns unique ids to each spider job, workarounds some Scrapy
    issues and provides extra stats.
    """
    crawl_ids = itertools.count(start=1)

    def __init__(self, settings=None):
        self.signals = SignalManager(self)
        self.signals.connect(self.on_spider_closed, CrawlerProcessSignals.spider_closed)
        self._finished_jobs = []
        super(ArachnadoCrawlerProcess, self).__init__(settings or {})

    def crawl(self, crawler_or_spidercls, *args, **kwargs):
        kwargs['crawl_id'] = next(self.crawl_ids)

        crawler = crawler_or_spidercls
        if not isinstance(crawler_or_spidercls, Crawler):
            crawler = self._create_crawler(crawler_or_spidercls)

        for name in SIGNAL_NAMES:
            crawler.signals.connect(self._resend_signal, getattr(signals, name))

        d = super(ArachnadoCrawlerProcess, self).crawl(crawler_or_spidercls, *args, **kwargs)
        return d

    def _resend_signal(self, **kwargs):
        cp_signal = CrawlerProcessSignals.signal(kwargs['signal'])
        kwargs['signal'] = cp_signal
        kwargs['crawler'] = kwargs.pop('sender')
        if cp_signal.supports_defer:
            return self.signals.send_catch_log_deferred(**kwargs)
        else:
            return self.signals.send_catch_log(**kwargs)

    def stop(self):
        """ Terminate the process (exit from application). """
        # a workaround for https://github.com/scrapy/scrapy/issues/1279
        d = super(ArachnadoCrawlerProcess, self).stop()
        d.addBoth(self._stop_reactor)
        return d

    def on_spider_closed(self, spider, reason):
        self._finished_jobs.append({
            'id': spider.crawl_id,
            'seed': spider.domain,
            'status': reason,
        })

    # def on_spider_opened(self, spider):
    #     logger.debug("on_spider_opened")
    #
    # def on_spider_idle(self, spider):
    #     logger.debug("on_spider_idle")
    #
    # def on_spider_error(self, failure, response, spider):
    #     logger.debug("on_spider_error")
    #
    # def on_request_scheduled(self, request, spider):
    #     pass
    #     # logger.debug("on_request_scheduled")
    #
    # def on_request_dropped(self, request, spider):
    #     pass
    #     # logger.debug("on_request_dropped")
    #
    # def on_response_received(self, response, request, spider):
    #     logger.debug("on_response_received")
    #
    # def on_response_downloaded(self, response, request, spider):
    #     logger.debug("on_response_downloaded")
    #
    # def on_item_scraped(self, item, response, spider):
    #     logger.debug("on_item_scraped")
    #
    # def on_item_dropped(self, item, response, exception, spider):
    #     logger.debug("on_item_dropped")

    @property
    def finished_jobs(self):
        return self._finished_jobs

    @property
    def active_jobs(self):
        """ Return a list of active jobs """
        spiders = [c.spider for c in self.crawlers if c.spider is not None]
        return [
            {'id': sp.crawl_id, 'status': 'crawling', 'seed': sp.domain}
            for sp in spiders
        ]

    @property
    def jobs(self):
        """ Current crawl state """

        # filter out active jobs which are in fact finished
        finished_ids = {job['id'] for job in self.finished_jobs}
        active_jobs = [job for job in self.active_jobs
                       if job['id'] not in finished_ids]

        return active_jobs + self.finished_jobs
