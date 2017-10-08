import logging
import numpy as np
from email.utils import formatdate
from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
        ConnectionRefusedError, ConnectionDone, ConnectError, \
        ConnectionLost, TCPTimedOutError

from scrapy import signals
from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapy.utils.misc import load_object
from scrapy.xlib.tx import ResponseFailed

from arachnado.pagecache.composite import CompositeCacheStorage


logger = logging.getLogger(__name__)


class HttpCacheMiddleware(object):
    use_depth = False
    depth_prob_start = 0
    DOWNLOAD_EXCEPTIONS = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError)

    def __init__(self, settings, stats):
        if not settings.getbool('HTTPCACHE_ENABLED'):
            raise NotConfigured
        self.use_depth = settings.get('HTTPCACHE_DEPTH_PROB', False)
        self.depth_prob_start = settings.get('HTTPCACHE_DEPTH_PROB_START', 0.05)
        self.policy = load_object(settings['HTTPCACHE_POLICY'])(settings)
        self.storage = load_object(settings['HTTPCACHE_STORAGE'])(settings)
        self.ignore_missing = settings.getbool('HTTPCACHE_IGNORE_MISSING')
        self.stats = stats
        logger.info("HTTP cache initialted")
        logger.info(type(self.storage))

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.settings, crawler.stats)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def get_eps(self, depth):
        eps = self.depth_prob_start + depth / 7
        if eps > 1:
            return 1.0
        else:
            return eps

    def spider_opened(self, spider):
        self.storage.open_spider(spider)

    def spider_closed(self, spider):
        self.storage.close_spider(spider)

    def process_request(self, request, spider):
        if request.meta.get('dont_cache', False):
            return

        # Skip uncacheable requests
        if not self.policy.should_cache_request(request):
            request.meta['_dont_cache'] = True  # flag as uncacheable
            return
        # probability decision to use cache
        if self.use_depth:
            depth = request.meta.get("depth", 0)
            eps = self.get_eps(depth)
            _r = np.random.rand()
            # logger.warning("{}, {}, {}".format(depth, eps, _r))
            if _r > eps:
                self.stats.inc_value('httpcache/prob/skip', spider=spider)
                # logger.warning("We will not use cache")
                return
            else:
                self.stats.inc_value('httpcache/prob/usage', spider=spider)
                pass
                # logger.warning("We will use cache")
        # Look for cached response and check if expired
        cachedresponse = self.storage.retrieve_response(spider, request)
        if self.stats:
            if isinstance(self.storage, CompositeCacheStorage):
                self.stats.set_value('httpcache/temp/hits',
                                     self.storage.temp_collection_used,
                                     spider=spider)
                self.stats.set_value('httpcache/perm/hits',
                                     self.storage.perm_collection_used,
                                     spider=spider)
                self.stats.set_value('httpcache/temp/errors',
                                     self.storage.temp_collection_errors,
                                     spider=spider)
                self.stats.set_value('httpcache/perm/errors',
                                     self.storage.perm_collection_errors,
                                     spider=spider)

        if cachedresponse is None:
            self.stats.inc_value('httpcache/miss', spider=spider)
            if self.ignore_missing:
                self.stats.inc_value('httpcache/ignore', spider=spider)
                raise IgnoreRequest("Ignored request not in cache: %s" % request)
            return  # first time request
        # Return cached response only if not expired
        cachedresponse.flags.append('cached')
        if self.policy.is_cached_response_fresh(cachedresponse, request):
            self.stats.inc_value('httpcache/hit', spider=spider)
            return cachedresponse
        # Keep a reference to cached response to avoid a second cache lookup on
        # process_response hook
        request.meta['cached_response'] = cachedresponse

    def process_response(self, request, response, spider):
        if request.meta.get('dont_cache', False):
            return response

        # Skip cached responses and uncacheable requests
        if 'cached' in response.flags or '_dont_cache' in request.meta:
            request.meta.pop('_dont_cache', None)
            return response

        # RFC2616 requires origin server to set Date header,
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.18
        if 'Date' not in response.headers:
            response.headers['Date'] = formatdate(usegmt=1)

        # Do not validate first-hand responses
        cachedresponse = request.meta.pop('cached_response', None)
        if cachedresponse is None:
            self.stats.inc_value('httpcache/firsthand', spider=spider)
            self._cache_response(spider, response, request, cachedresponse)
            return response

        if self.policy.is_cached_response_valid(cachedresponse, response, request):
            self.stats.inc_value('httpcache/revalidate', spider=spider)
            return cachedresponse

        self.stats.inc_value('httpcache/invalidate', spider=spider)
        self._cache_response(spider, response, request, cachedresponse)
        return response

    def process_exception(self, request, exception, spider):
        cachedresponse = request.meta.pop('cached_response', None)
        if cachedresponse is not None and isinstance(exception, self.DOWNLOAD_EXCEPTIONS):
            self.stats.inc_value('httpcache/errorrecovery', spider=spider)
            return cachedresponse

    def _cache_response(self, spider, response, request, cachedresponse):
        if self.policy.should_cache_response(response, request):
            self.stats.inc_value('httpcache/store', spider=spider)
            self.storage.store_response(spider, request, response)
        else:
            self.stats.inc_value('httpcache/uncacheable', spider=spider)
