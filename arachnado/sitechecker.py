from datetime import datetime
from urlparse import urlparse

import scrapy
import pymongo
from bson.objectid import ObjectId
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


sites_updated = object()
site_added = object()
site_removed = object()
site_changed = object()


DEFAULT_SETTINGS = {
    'DOWNLOAD_TIMEOUT': 60
}


def get_site_checker_crawler():
    return SiteCheckerCrawler(SiteCheckerSpider, DEFAULT_SETTINGS)


class SiteCheckerCrawler(Crawler):

    def __init__(self, *args, **kwargs):
        super(SiteCheckerCrawler, self).__init__(*args, **kwargs)
        mongo_uri = self.settings.get('SITECHECKER_MONGO_URI',
                                      'mongo://localhost:27017/arachnado')
        parsed = urlparse(mongo_uri)
        mongo = pymongo.MongoClient(parsed.netloc, parsed.port)
        self.db = mongo[parsed.path.lstrip('/')]
        self.signals.connect(self.item_scraped,
                             signal=signals.item_scraped)

    def item_scraped(self, item):
        self.db.sites.replace_one({'_id': ObjectId(item['_id'])}, dict(item))
        self.send_catch_log(site_changed)


class SiteCheckerSpider(scrapy.Spider):
    name = 'site-checker'
    net_exceptions = (TimeoutError, DNSLookupError,
                      ConnectionRefusedError, ConnectionDone, ConnectError,
                      ConnectionLost, TCPTimedOutError, ResponseFailed,
                      IOError)

    def __init__(self, *args, **kwargs):
        super(SiteCheckerSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        self.crawler.signals.connect(self.spider_idle,
                                     signal=signals.spider_idle)
        for signal in (site_added, site_removed, site_changed):
            self.crawler.signals.connect(self.run_checks, signal=signal)
        self.sites = {}
        self.running_ids = set()
        self.default_check_interval = 5
        # self.sites['abc'] = {
        #     '_id': 'abc',
        #     'url': 'http://fasdlkfjasdlkfjasdlkfjsdklf.com'
        # }
        return []

    def spider_idle(self):
        print 'idle'
        self.run_checks(self.sites)
        raise DontCloseSpider

    def run_checks(self, sites):
        self.sites = sites
        for site in sites.itervalues():
            if site['_id'] not in self.running_ids:
                self.running_ids.add(site['_id'])
                self.run_check(site)
        # Remove deleted checks from running_ids
        self.running_ids &= set(sites.iterkeys())

    def parse_site(self, response):
        id_ = response.meta['_id']
        site = self.sites.get(id_)
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
        self.rerun_check(self.sites[request.meta['_id']])
        return {
            '_id': request.meta['_id'],
            'status': response.status if response else 'unavailable',
            'error': failure.getErrorMessage(),
            'updated_at': datetime.now(),
        }

    def run_check(self, site):
        print 'run check'
        request = scrapy.Request(
            url=site['url'],
            callback=self.parse_site,
            errback=self.parse_site_error,
            dont_filter=True,
            meta={'_id': site['_id']}
        )
        self.crawler.engine.crawl(request, self)

    def rerun_check(self, site):
        check_interval = site.get('check_interval',
                                  self.default_check_interval)
        reactor.callLater(check_interval, self.run_check, site)

    def detect_engine(self, body):
        return 'test', {'abc': 1}
