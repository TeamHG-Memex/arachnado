from copy import deepcopy
from datetime import datetime
from urlparse import urlparse
from collections import OrderedDict

import scrapy
import motor
import logging
from bson.objectid import ObjectId
from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from scrapy.crawler import Crawler
from scrapy.xlib.tx import ResponseFailed
from scrapy.signalmanager import SignalManager
from twisted.internet import reactor
from twisted.internet.error import (
    TimeoutError, DNSLookupError,
    ConnectionRefusedError, ConnectionDone, ConnectError,
    ConnectionLost, TCPTimedOutError
)
from tornado.gen import Return, coroutine
from bot_detector.detector import Detector

from arachnado.utils.twistedtornado import tt_coroutine
from arachnado.wsbase import BaseWSHandler

site_created = object()
site_updated = object()
site_deleted = object()
sites_fetched = object()


DEFAULT_SETTINGS = {
    'DOWNLOAD_TIMEOUT': 60
}


def get_site_checker_crawler():
    site_signals = SignalManager()
    return SiteCheckerCrawler(
        MongodbStorage('mongo://localhost:27017/arachnado', site_signals),
        site_signals,
        SiteCheckerSpider,
        DEFAULT_SETTINGS
    )


def replace_dots(son):
    """Recursively replace keys that contains dots"""
    for key, value in son.items():
        if '.' in key:
            new_key = key.replace('.', '_')
            if isinstance(value, dict):
                son[new_key] = replace_dots(
                    son.pop(key)
                )
            else:
                son[new_key] = son.pop(key)
        elif isinstance(value, dict):  # recurse into sub-docs
            son[key] = replace_dots(value)
    return son


class MongodbStorage(object):

    def __init__(self, mongo_uri, signals):
        parsed = urlparse(mongo_uri)
        mongo = motor.MotorClient(parsed.netloc, parsed.port)
        self.db = mongo[parsed.path.lstrip('/')]
        self.col = self.db.sites
        self.signals = signals

    @coroutine
    def list(self):
        docs = []
        cursor = self.col.find()
        while (yield cursor.fetch_next):
            docs.append(cursor.next_object())
        self.signals.send_catch_log(sites_fetched, sites=docs)
        raise Return(docs)

    @coroutine
    def create(self, doc):
        doc = replace_dots(doc)
        result = yield self.col.insert(doc)
        self.signals.send_catch_log(site_created, site=doc)
        raise Return(result)

    @coroutine
    def update(self, doc):
        doc = replace_dots(doc)
        doc_copy = deepcopy(doc)
        doc_copy.pop('_id')
        result = yield self.col.update({
            '_id': ObjectId(doc['_id'])
        }, {
            '$set': doc_copy
        })
        self.signals.send_catch_log(site_updated, site=doc)
        raise Return(result)

    @coroutine
    def delete(self, site):
        result = yield self.col.remove({'_id': ObjectId(site['_id'])})
        self.signals.send_catch_log(site_deleted, site=site)
        raise Return(result)


class SiteCheckerCrawler(Crawler):

    def __init__(self, storage, site_signals, *args, **kwargs):
        super(SiteCheckerCrawler, self).__init__(*args, **kwargs)
        self.storage = storage
        self.sites = OrderedDict()
        self.schedule = {}
        self.site_signals = site_signals
        self.signals.connect(self.item_scraped,
                             signal=signals.item_scraped)
        self.signals.connect(self.open_spider,
                             signal=signals.spider_opened)
        self.site_signals.connect(self.site_created, site_created)
        self.site_signals.connect(self.site_deleted, site_deleted)
        self.site_signals.connect(self.site_updated, site_updated)

    @tt_coroutine
    def open_spider(self, spider, *args, **kwargs):
        sites = yield self.storage.list()
        for site in sites:
            self.sites[str(site['_id'])] = site
        self.sites_updated()

    def item_scraped(self, item):
        self.storage.update(dict(item))

    def site_updated(self, site):
        self.sites[str(site['_id'])].update(site)
        self.sites_updated()

    def site_deleted(self, site):
        self.sites.pop(str(site['_id']), None)
        self.sites_updated()

    def site_created(self, site):
        self.sites[str(site['_id'])] = site
        self.sites_updated()

    def sites_updated(self):
        if self.spider:
            self.spider.run_checks(self.sites)


class SiteCheckerSpider(scrapy.Spider):
    name = 'site-checker'
    net_exceptions = (TimeoutError, DNSLookupError,
                      ConnectionRefusedError, ConnectionDone, ConnectError,
                      ConnectionLost, TCPTimedOutError, ResponseFailed,
                      IOError)

    def __init__(self, *args, **kwargs):
        super(SiteCheckerSpider, self).__init__(*args, **kwargs)
        self.detector = Detector()
        logging.getLogger("scrapy.core.scraper").setLevel(logging.INFO)

    def start_requests(self):
        self.crawler.signals.connect(self.spider_idle,
                                     signal=signals.spider_idle)
        self.running_ids = set()
        self.default_check_interval = 60
        return []

    def spider_idle(self):
        self.run_checks(self.crawler.sites)
        raise DontCloseSpider

    def run_checks(self, sites):
        for site in sites.itervalues():
            if str(site['_id']) not in self.running_ids:
                self.running_ids.add(str(site['_id']))
                self.run_check(site)
        # Remove deleted checks from running_ids
        self.running_ids &= set(sites.iterkeys())

    def parse_site(self, response):
        id_ = str(response.meta['_id'])
        site = self.crawler.sites.get(id_)
        if not site:  # Site was removed
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
            'updated_at': datetime.now(),
        }

    def parse_site_error(self, failure):
        request = failure.request
        response = getattr(failure, 'response', None)
        self.rerun_check(self.crawler.sites[str(request.meta['_id'])])
        return {
            '_id': str(request.meta['_id']),
            'status': response.status if response else 'unavailable',
            'error': failure.getErrorMessage(),
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
        result = self.detector.detect(body)
        if result is None:
            return 'generic', {}
        return result


class WSHandler(BaseWSHandler):
    """
    WebSocket handler which pushes Sites change events to a client.
    """

    def initialize(self, site_checker_crawler, **kwargs):
        self.crawler = site_checker_crawler

    def on_open(self):
        self.crawler.site_signals.connect(self.on_site_created, site_created)
        self.crawler.site_signals.connect(self.on_site_updated, site_updated)
        self.crawler.site_signals.connect(self.on_site_deleted, site_deleted)

        self.write_event("sites:set", self.crawler.sites.values())

    def on_close(self):
        self.crawler.site_signals.disconnect(self.on_site_created,
                                             site_created)
        self.crawler.site_signals.disconnect(self.on_site_updated,
                                             site_updated)
        self.crawler.site_signals.disconnect(self.on_site_deleted,
                                             site_deleted)

    def on_site_created(self, site):
        self.write_event('sites:created', site)

    def on_site_updated(self, site):
        self.write_event('sites:updated', site)

    def on_site_deleted(self, site):
        self.write_event('sites:deleted', site)
