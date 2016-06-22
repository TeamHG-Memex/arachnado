from datetime import datetime

import scrapy
import logging
from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from scrapy.crawler import Crawler
from scrapy.xlib.tx import ResponseFailed
from twisted.internet import reactor
from twisted.internet.error import (
    TimeoutError, DNSLookupError,
    ConnectionRefusedError, ConnectionDone, ConnectError,
    ConnectionLost, TCPTimedOutError
)

from arachnado.utils.twistedtornado import tt_coroutine


logger = logging.getLogger(__name__)


DEFAULT_SETTINGS = {
    'DOWNLOAD_TIMEOUT': 60,
}


def get_site_checker_crawler(storage):
    return SiteCheckerCrawler(
        storage,
        SiteCheckerSpider,
        DEFAULT_SETTINGS
    )


class SiteCheckerCrawler(Crawler):

    def __init__(self, storage, *args, **kwargs):
        super(SiteCheckerCrawler, self).__init__(*args, **kwargs)
        self.storage = storage
        self.schedule = {}
        self.signals.connect(self.item_scraped,
                             signal=signals.item_scraped)
        self.signals.connect(self.open_spider,
                             signal=signals.spider_opened)
        self.storage.subscribe(['created', 'deleted', 'updated'],
                               self.sites_updated)

    @tt_coroutine
    def open_spider(self, spider, *args, **kwargs):
        try:
            yield self.storage.fetch()
        except Exception:
            logger.error(
                "Can't connect to %s. SiteChecked won't work.",
                self.storage.mongo_uri, exc_info=True,
            )
            raise

    def item_scraped(self, item):
        self.storage.update(dict(item))

    def sites_updated(self):
        if self.spider:
            self.spider.run_checks(self.storage.cache)


class SiteCheckerSpider(scrapy.Spider):
    name = 'site-checker'
    handle_httpstatus_list = list(range(100, 300)) + list(range(400, 600))
    error_messages = {
        TimeoutError: 'timeout',
        DNSLookupError: 'host not found',
        ConnectionRefusedError: 'connection refused',
        ConnectionDone: 'connection done',
        ConnectError: 'connect error',
        ConnectionLost: 'connection lost',
        TCPTimedOutError: 'timeout',
        ResponseFailed: 'response failed',
        IOError: 'io error',
    }

    def __init__(self, *args, **kwargs):
        super(SiteCheckerSpider, self).__init__(*args, **kwargs)
        try:
            from bot_detector.detector import Detector
            self.detector = Detector()
        except ImportError:
            self.detector = None
        logging.getLogger("scrapy.core.scraper").setLevel(logging.INFO)

    def start_requests(self):
        self.crawler.signals.connect(self.spider_idle,
                                     signal=signals.spider_idle)
        self.running_ids = set()
        self.default_check_interval = 60
        return []

    def spider_idle(self):
        self.run_checks(self.crawler.storage.cache)
        raise DontCloseSpider

    def run_checks(self, sites):
        for site in sites.values():
            if str(site['_id']) not in self.running_ids:
                self.running_ids.add(str(site['_id']))
                self.run_check(site)
        # Remove deleted checks from running_ids
        self.running_ids &= set(sites.keys())

    def parse_site(self, response):
        id_ = str(response.meta['_id'])
        try:
            site = self.crawler.storage.cache[id_]
        except KeyError:
            return
        engine, features = self.detect_engine(response.body)
        title = response.xpath('//title/text()').extract_first()
        latency = response.meta.get('download_latency')
        self.rerun_check(site)
        return {
            '_id': id_,
            'title': title,
            'engine': engine,
            'features': features,
            'latency': latency,
            'status': response.status,
            'error': None,
            'updated_at': datetime.now(),
        }

    def parse_site_error(self, failure):
        error_message = self.error_messages.get(failure.type, 'unknown error')
        request = failure.request
        try:
            site = self.crawler.storage.cache[str(request.meta['_id'])]
        except KeyError:
            return
        self.rerun_check(site)
        return {
            '_id': str(request.meta['_id']),
            'title': None,
            'engine': None,
            'features': None,
            'latency': None,
            'status': 'unavailable',
            'error': error_message,
            'updated_at': datetime.now(),
        }

    def run_check(self, site):
        request = scrapy.Request(
            url=site['url'],
            callback=self.parse_site,
            errback=self.parse_site_error,
            dont_filter=True,
            meta={'_id': str(site['_id'])}
        )
        self.crawler.engine.crawl(request, self)

    def rerun_check(self, site):
        check_interval = site.get('check_interval',
                                  self.default_check_interval)
        reactor.callLater(check_interval, self.run_check, site)

    def detect_engine(self, body):
        result = self.detector.detect(body) if self.detector else None
        if result is None:
            return None, {}
        return result
