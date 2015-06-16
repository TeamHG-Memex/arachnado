# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import itertools
import six

from scrapy import signals
from scrapy.signalmanager import SignalManager
from scrapy.crawler import CrawlerProcess, Crawler
from scrapy.core.engine import ExecutionEngine

from arachnado.signals import Signal
from arachnado import stats
from arachnado.process_stats import ProcessStatsMonitor

logger = logging.getLogger(__name__)

# monkey patch Scrapy to add an extra signal
signals.spider_closing = object()


# a signal which is fired when stats are changed in any of the spiders
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
    'spider_closing',  # custom
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
        spider_closing = Signal('spider_closing', False)  # custom
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


class ArachnadoExecutionEngine(ExecutionEngine):
    """
    Extended ExecutionEngine.
    It sends a signal when engine gets scheduled to stop.
    """
    def close_spider(self, spider, reason='cancelled'):
        if self.slot.closing:
            return self.slot.closing
        self.crawler.crawling = False
        self.signals.send_catch_log(signals.spider_closing)
        return super(ArachnadoExecutionEngine, self).close_spider(spider, reason)


class ArachnadoCrawler(Crawler):
    """
    Extended Crawler.
    It sends a signal when engine gets scheduled to stop.
    """
    def _create_engine(self):
        return ArachnadoExecutionEngine(self, lambda _: self.stop())


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

        # don't log DepthMiddleware messages
        # see https://github.com/scrapy/scrapy/issues/1308
        logging.getLogger("scrapy.spidermiddlewares.depth").setLevel(logging.INFO)

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

    def _create_crawler(self, spidercls):
        if isinstance(spidercls, six.string_types):
            spidercls = self.spider_loader.load(spidercls)
        return ArachnadoCrawler(spidercls, self.settings)

    def stop_job(self, crawl_id):
        """ Stop a single crawl job """
        for crawler in self.crawlers:
            if getattr(crawler.spider, "crawl_id") == crawl_id:
                return crawler.stop()

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
        self.procmon.stop()
        return super(ArachnadoCrawlerProcess, self).stop()

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
        crawlers = [cr for cr in self.crawlers if cr.spider is not None]
        return [
            {
                'id': cr.spider.crawl_id,
                'seed': cr.spider.domain,
                'status': 'crawling' if cr.crawling else 'stopping',
                'stats': cr.spider.crawler.stats.get_stats(cr.spider),
            }
            for cr in crawlers
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
