# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import operator

import six
from twisted.internet import defer
from scrapy.core.downloader import Downloader
from scrapy.utils.reactor import CallLaterOnce
from scrapy import signals
from scrapy.signalmanager import SignalManager
from scrapy.crawler import CrawlerProcess, Crawler
from scrapy.core.engine import ExecutionEngine
# from scrapy.utils.engine import get_engine_status

from arachnado.signals import Signal
from arachnado import stats
from arachnado.process_stats import ProcessStatsMonitor

logger = logging.getLogger(__name__)

# monkey patch Scrapy to add extra signals
signals.spider_closing = object()
signals.engine_paused = object()
signals.engine_resumed = object()
signals.engine_tick = object()
signals.downloader_enqueued = object()
signals.downloader_dequeued = object()


# a signal which is fired when stats are changed in any of the spiders
agg_stats_changed = Signal("agg_stats_changed", False)
STAT_SIGNALS = {
    stats.stats_changed: agg_stats_changed,
}


SCRAPY_SIGNAL_NAMES = [
    'engine_started',
    'engine_stopped',
    'engine_paused',  # custom
    'engine_resumed',  # custom
    'engine_tick',  # custom
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
    'downloader_enqueued',  # custom
    'downloader_dequeued',  # custom
]


def _get_crawler_process_signals_cls():
    spider_to_cp = {}

    class CrawlerProcessSignals(object):
        @classmethod
        def signal(cls, spider_signal):
            return spider_to_cp[spider_signal]

        engine_started = Signal('engine_started', True)
        engine_stopped = Signal('engine_stopped', True)
        engine_paused = Signal('engine_paused', False)  # custom
        engine_resumed = Signal('engine_resumed', False)  # custom
        engine_tick = Signal('engine_tick', False)  # custom
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
        downloader_enqueued = Signal('downloader_enqueued', False)
        downloader_dequeued = Signal('downloader_dequeued', False)

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
    def __init__(self, *args, **kwargs):
        super(ArachnadoExecutionEngine, self).__init__(*args, **kwargs)
        self.send_tick = CallLaterOnce(self._send_tick_signal)

    def close_spider(self, spider, reason='cancelled'):
        if self.slot.closing:
            return self.slot.closing
        self.crawler.crawling = False
        dfd = self.signals.send_catch_log_deferred(signals.spider_closing,
                                                   spider=spider,
                                                   reason=reason)
        dfd.addBoth(
            lambda _: super(ArachnadoExecutionEngine, self).close_spider(spider, reason)
        )
        return dfd

    def pause(self):
        """Pause the execution engine"""
        super(ArachnadoExecutionEngine, self).pause()
        self.signals.send_catch_log(signals.engine_paused)

    def unpause(self):
        """Resume the execution engine"""
        super(ArachnadoExecutionEngine, self).unpause()
        self.signals.send_catch_log(signals.engine_resumed)

    def _next_request(self, spider):
        res = super(ArachnadoExecutionEngine, self)._next_request(spider)
        self.send_tick.schedule(0.1)  # avoid sending the signal too often
        return res

    def _send_tick_signal(self):
        self.signals.send_catch_log_deferred(signals.engine_tick)


class ArachnadoCrawler(Crawler):
    """
    Extended Crawler which uses ArachnadoExecutionEngine.
    """
    # Should be set by caller. Currently DomainCrawlers class sets it (ugly).
    start_options = None

    def _create_engine(self):
        return ArachnadoExecutionEngine(self, lambda _: self.stop())


class ArachnadoDownloader(Downloader):
    def _enqueue_request(self, request, spider):
        dfd = super(ArachnadoDownloader, self)._enqueue_request(request,
                                                                spider)
        self.signals.send_catch_log(signals.downloader_enqueued)

        def _send_dequeued(_):
            self.signals.send_catch_log(signals.downloader_dequeued)
            return _

        dfd.addBoth(_send_dequeued)
        return dfd


class ArachnadoCrawlerProcess(CrawlerProcess):
    """
    CrawlerProcess which sets up a global signals manager,
    assigns unique ids to each spider job, workarounds some Scrapy
    issues and provides extra stats.
    """
    def __init__(self, settings=None):
        self.signals = SignalManager(self)
        self.signals.connect(self.on_spider_closed,
                             CrawlerProcessSignals.spider_closed)
        self._finished_jobs = []
        self._paused_jobs = set()
        self.procmon = ProcessStatsMonitor()
        self.procmon.start()

        super(ArachnadoCrawlerProcess, self).__init__(settings)

        # don't log DepthMiddleware messages
        # see https://github.com/scrapy/scrapy/issues/1308
        logger_ = logging.getLogger("scrapy.spidermiddlewares.depth")
        logger_.setLevel(logging.INFO)

    def crawl(self, crawler_or_spidercls, *args, **kwargs):
        crawler = self.create_crawler(crawler_or_spidercls)

        # aggregate all crawler signals
        for name in SCRAPY_SIGNAL_NAMES:
            crawler.signals.connect(self._resend_signal,
                                    getattr(signals, name))

        # aggregate signals from crawler EventedStatsCollectors
        if hasattr(crawler.stats, "signals"):
            crawler.stats.signals.connect(
                self._resend_signal, stats.stats_changed
            )

        d = super(ArachnadoCrawlerProcess, self).crawl(crawler, *args, **kwargs)
        return d

    def _create_crawler(self, spidercls):
        # this is overridden to create ArachnadoCrawler instead of Crawler
        if isinstance(spidercls, six.string_types):
            spidercls = self.spider_loader.load(spidercls)
        return ArachnadoCrawler(spidercls, self.settings)

    def stop_job(self, crawl_id):
        """ Stop a single crawl job """
        crawler = self.get_crawler(crawl_id)
        dfd = crawler.engine.close_spider(crawler.spider, 'stopped')
        dfd.addBoth(lambda _: crawler.stop())
        return dfd

    def pause_job(self, crawl_id):
        """ Pause a crawling job """
        self._paused_jobs.add(crawl_id)
        self.get_crawler(crawl_id).engine.pause()

    def resume_job(self, crawl_id):
        """ Resume a crawling job """
        self._paused_jobs.remove(crawl_id)
        self.get_crawler(crawl_id).engine.unpause()

    def get_crawler(self, crawl_id):
        if crawl_id is not None:
            for crawler in self.crawlers:
                if getattr(crawler.spider, "crawl_id", None) == crawl_id:
                    return crawler
        raise KeyError("Job is not known: %s" % crawl_id)

    def _resend_signal(self, **kwargs):
        # FIXME: this is a mess. Signal handling should be unified somehow:
        # there shouldn't be two separate code paths
        # for CrawlerProcessSignals and STAT_SIGNALS.
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
        if isinstance(spider.crawler, ArachnadoCrawler):
            self._finished_jobs.insert(0, self._get_job_info(spider.crawler,
                                                             reason))

    # FIXME: methods below are ugly for two reasons:
    # 1. they assume spiders have certain attributes;
    # 2. they try to get crawling status based on auxilary information.
    #
    # Time to move them to DomainCrawler?

    def get_jobs(self):
        """ Return a list of active jobs """
        crawlers = [crawler for crawler in self.crawlers
                    if crawler.spider is not None and
                    isinstance(crawler, ArachnadoCrawler)]
        return [self._get_job_info(crawler, self._get_crawler_status(crawler))
                for crawler in crawlers]

    def _get_job_info(self, crawler, status):
        start_options = getattr(crawler, 'start_options', {})
        return {
            'id': crawler.spider.crawl_id,
            'job_id': getattr(crawler.spider, 'motor_job_id'),
            'seed': crawler.spider.domain,
            'status': status,
            'stats': crawler.stats.get_stats(crawler.spider),
            'downloads': self._downloader_stats(crawler),
            'args': start_options.get('args', {}),
            'settings': start_options.get('settings', {}),
            # 'start_options': start_options,
            # 'engine_info': dict(get_engine_status(crawler.engine))
        }

    @classmethod
    def _downloader_stats(cls, crawler):
        downloader = crawler.engine.downloader
        return {
            'active': [cls._request_info(req) for req in downloader.active],
            'slots': sorted([
                cls._slot_info(key, slot)
                for key, slot in downloader.slots.items()
            ], key=operator.itemgetter('key'))
        }

    @classmethod
    def _request_info(cls, request):
        info = {'url': request.url, 'method': request.method}
        if 'splash' in request.meta:
            splash_args = request.meta['splash'].get('args', {})
            if 'url' in splash_args:
                info['url'] = splash_args['url']
            info['method'] = splash_args.get('http_method', 'GET')
        return info

    @classmethod
    def _slot_info(cls, key, slot):
        return {
            'key': key,
            'concurrency': slot.concurrency,
            'delay': slot.delay,
            'lastseen': slot.lastseen,
            'len(queue)': len(slot.queue),
            'transferring': [cls._request_info(req)
                             for req in slot.transferring],
            'active': [cls._request_info(req) for req in slot.active],
        }

    def _get_crawler_status(self, crawler):
        if crawler.spider is None:
            return "unknown"
        if not crawler.crawling:
            return "stopping"
        if crawler.spider.crawl_id in self._paused_jobs:
            return "suspended"
        return "crawling"

    @property
    def jobs(self):
        """ Current crawl state """
        # filter out active jobs which are in fact finished
        finished_ids = {job['id'] for job in self._finished_jobs}
        active_jobs = [job for job in self.get_jobs()
                       if job['id'] not in finished_ids]

        return active_jobs + self._finished_jobs
