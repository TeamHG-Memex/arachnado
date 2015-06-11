# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import itertools

from scrapy import signals
from scrapy.signalmanager import SignalManager
from scrapy.crawler import CrawlerProcess, Crawler

from arachnado.signals import Signal
from arachnado import stats
from arachnado.process_stats import ProcessStatsMonitor

logger = logging.getLogger(__name__)


agg_stats_changed = Signal("agg_stats_changed", False)
STAT_SIGNALS = {
    stats.stats_changed: agg_stats_changed,
}


SCRAPY_SIGNAL_NAMES = [
    'engine_started',
    'engine_stopped',
    'item_scraped',
    'item_dropped',
    'spider_closed',
    'spider_opened',
    'spider_idle',
    'spider_error',
    'request_scheduled',
    'request_dropped',
    'response_received',
    'response_downloaded',
]


def _get_crawler_process_signals_cls():
    spider_to_cp = {}

    class CrawlerProcessSignals(object):
        @classmethod
        def signal(cls, spider_signal):
            return spider_to_cp[spider_signal]

        engine_started = Signal('engine_started', True)
        engine_stopped = Signal('engine_stopped', True)
        spider_opened = Signal('spider_opened', True)
        spider_idle = Signal('spider_idle', False)
        spider_closed = Signal('spider_closed', True)
        spider_error = Signal('spider_error', False)
        request_scheduled = Signal('request_scheduled', False)
        request_dropped = Signal('request_dropped', False)
        response_received = Signal('response_received', False)
        response_downloaded = Signal('response_downloaded', False)
        item_scraped = Signal('item_scraped', True)
        item_dropped = Signal('item_dropped', True)

    for name in SCRAPY_SIGNAL_NAMES:
        signal = getattr(signals, name)
        cp_signal = getattr(CrawlerProcessSignals, name)
        spider_to_cp[signal] = cp_signal

    return CrawlerProcessSignals


CrawlerProcessSignals = _get_crawler_process_signals_cls()


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
        self.procmon = ProcessStatsMonitor()
        self.procmon.start()
        super(ArachnadoCrawlerProcess, self).__init__(settings or {})

    def crawl(self, crawler_or_spidercls, *args, **kwargs):
        kwargs['crawl_id'] = next(self.crawl_ids)

        crawler = crawler_or_spidercls
        if not isinstance(crawler_or_spidercls, Crawler):
            crawler = self._create_crawler(crawler_or_spidercls)

        # aggregate all crawler signals
        for name in SCRAPY_SIGNAL_NAMES:
            crawler.signals.connect(self._resend_signal, getattr(signals, name))

        # aggregate signals from crawler EventedStatsCollectors
        if hasattr(crawler.stats, "signals"):
            crawler.stats.signals.connect(self._resend_signal, stats.stats_changed)

        d = super(ArachnadoCrawlerProcess, self).crawl(crawler_or_spidercls, *args, **kwargs)
        return d

    def _resend_signal(self, **kwargs):
        # FIXME: this is a mess. Signal handling should be unified somehow.
        signal = kwargs['signal']
        if signal in STAT_SIGNALS:
            signal = STAT_SIGNALS[signal]
            kwargs['crawler'] = kwargs.pop('sender').crawler
        else:
            signal = CrawlerProcessSignals.signal(signal)
            kwargs['crawler'] = kwargs.pop('sender')

        kwargs['signal'] = signal
        if signal.supports_defer:
            return self.signals.send_catch_log_deferred(**kwargs)
        else:
            return self.signals.send_catch_log(**kwargs)

    def stop(self):
        """ Terminate the process (exit from application). """
        # a workaround for https://github.com/scrapy/scrapy/issues/1279
        self.procmon.stop()
        d = super(ArachnadoCrawlerProcess, self).stop()
        d.addBoth(self._stop_reactor)
        return d

    def on_spider_closed(self, spider, reason):
        # spiders are closed not that often, insert(0,...) should be fine
        self._finished_jobs.insert(0, {
            'id': spider.crawl_id,
            'seed': spider.domain,
            'status': reason,
            'stats': spider.crawler.stats.get_stats(spider),
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
            {
                'id': spider.crawl_id,
                'seed': spider.domain,
                'status': 'crawling',
                'stats': spider.crawler.stats.get_stats(spider),
            }
            for spider in spiders
        ]

    @property
    def jobs(self):
        """ Current crawl state """

        # FIXME: this is ugly
        # filter out active jobs which are in fact finished
        finished_ids = {job['id'] for job in self.finished_jobs}
        active_jobs = [job for job in self.active_jobs
                       if job['id'] not in finished_ids]

        return active_jobs + self.finished_jobs
