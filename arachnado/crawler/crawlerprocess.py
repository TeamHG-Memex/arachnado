from __future__ import absolute_import
import re
import logging
import itertools
import operator
from os import getenv

import six
from scrapy import signals
from scrapy.signalmanager import SignalManager
from scrapy.crawler import CrawlerProcess, Crawler

from arachnado.process_stats import ProcessStatsMonitor
from arachnado.utils.spiders import get_spider_cls
from arachnado.spider import (
    ArachnadoSpider, CrawlWebsiteSpider, DEFAULT_SETTINGS
)
from arachnado.crawler.signals import SIGNALS
from arachnado.crawler.crawler import ArachnadoCrawler

logger = logging.getLogger(__name__)


class ArachnadoCrawlerProcess(CrawlerProcess):
    """
    CrawlerProcess which sets up a global signals manager,
    assigns unique ids to each spider job, workarounds some Scrapy
    issues and provides extra stats.
    """
    crawl_ids = itertools.count(start=1)

    def __init__(self, settings=None, opts=None):
        self.opts = opts or {}
        self.signals = SignalManager(self)
        self.signals.connect(self.on_spider_closed,
                             SIGNALS['spider_closed'])
        self._finished_jobs = []
        self._paused_jobs = set()
        self.procmon = ProcessStatsMonitor()
        self.procmon.start()

        super(ArachnadoCrawlerProcess, self).__init__(settings or {})

        # don't log DepthMiddleware messages
        # see https://github.com/scrapy/scrapy/issues/1308
        depth_logger = logging.getLogger("scrapy.spidermiddlewares.depth")
        depth_logger.setLevel(logging.INFO)

    def start_crawl(self, domain, args, settings):
        """
        Create, start and return crawler for given domain
        """
        storage_opts = self.opts['arachnado.mongo_export']
        settings.update({
            'MONGO_EXPORT_ENABLED': storage_opts['enabled'],
            'MONGO_EXPORT_JOBS_URI':
                getenv(storage_opts['jobs_mongo_uri_env']) or
                storage_opts['jobs_mongo_uri'],
            'MONGO_EXPORT_ITEMS_URI':
                getenv(storage_opts['items_mongo_uri_env']) or
                storage_opts['items_mongo_uri'],
        })
        spider_cls = get_spider_cls(domain, self._get_spider_package_names(),
                                    CrawlWebsiteSpider)

        if spider_cls is not None:
            crawler = self.create_crawler(settings, spider_cls=spider_cls)
            self.crawl(crawler, domain=domain, **args)
            return crawler

    def _get_spider_package_names(self):
        return [name for name in re.split(
            '\s+', self.opts['arachnado.scrapy']['spider_packages']
        ) if name]

    def create_crawler(self, settings=None, spider_cls=None):
        _settings = DEFAULT_SETTINGS.copy()
        _settings.update(settings or {})
        spider_cls = self._arachnadoize_spider_cls(spider_cls)
        return ArachnadoCrawler(spider_cls, _settings)

    def _arachnadoize_spider_cls(self, spider_cls):
        """
        Ensure that spider is inherited from ArachnadoSpider
        to receive its features
        """
        if not isinstance(spider_cls, ArachnadoSpider):
            return type(spider_cls.__name__, (spider_cls, ArachnadoSpider), {})
        return spider_cls

    def crawl(self, crawler_or_spidercls, *args, **kwargs):
        kwargs['crawl_id'] = next(self.crawl_ids)

        crawler = crawler_or_spidercls
        if not isinstance(crawler_or_spidercls, Crawler):
            crawler = self._create_crawler_from_spidercls(crawler_or_spidercls)

        # Forward crawler signals to self.signals
        for name, signal in SIGNALS.iteritems():
            scrapy_signal = getattr(signals, name, None)

            if scrapy_signal:
                crawler.signals.connect(
                    lambda **kwargs: self._forward_signal(signal),
                    scrapy_signal,
                    weak=False,
                )

        d = super(ArachnadoCrawlerProcess, self).crawl(
            crawler_or_spidercls, *args, **kwargs
        )
        return d

    def _create_crawler_from_spidercls(self, spidercls):
        if isinstance(spidercls, six.string_types):
            spidercls = self.spider_loader.load(spidercls)
        return ArachnadoCrawler(spidercls, self.settings)

    def stop_job(self, crawl_id):
        """ Stop a single crawl job """
        self.get_crawler(crawl_id).stop()

    def pause_job(self, crawl_id):
        """ Pause a crawling job """
        self._paused_jobs.add(crawl_id)
        self.get_crawler(crawl_id).engine.pause()

    def resume_job(self, crawl_id):
        """ Resume a crawling job """
        self._paused_jobs.remove(crawl_id)
        self.get_crawler(crawl_id).engine.unpause()

    def get_crawler(self, crawl_id):
        for crawler in self.crawlers:
            if getattr(crawler.spider, "crawl_id") == crawl_id:
                return crawler
        raise KeyError("Job is not known: %s" % crawl_id)

    def _forward_signal(self, signal, **kwargs):
        """Forward signal from ArachnadoCrawler to ArachnadoCrawlerProcess"""
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

    def get_jobs(self):
        """ Return a list of active jobs """
        crawlers = [crawler for crawler in self.crawlers
                    if crawler.spider is not None and
                    isinstance(crawler, ArachnadoCrawler)]
        return [self._get_job_info(crawler, self._get_crawler_status(crawler))
                for crawler in crawlers]

    def _get_job_info(self, crawler, status):
        return {
            'id': crawler.spider.crawl_id,
            'job_id': getattr(crawler.spider, 'motor_job_id'),
            'seed': crawler.spider.domain,
            'status': status,
            'stats': crawler.spider.crawler.stats.get_stats(crawler.spider),
            'downloads': self._downloader_stats(crawler),
            'flags': list(getattr(crawler.spider, 'flags', [])),
            'args': crawler.spider.kwargs,
            'settings': crawler.spider.user_settings,
            'login_url': (crawler.spider.login_form_response.url
                          if crawler.spider.login_form_response else None)
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
        return {'url': request.url, 'method': request.method}

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
        if int(crawler.spider.crawl_id) in self._paused_jobs:
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
