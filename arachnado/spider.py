# -*- coding: utf-8 -*-
from __future__ import absolute_import

import base64
import contextlib
import logging
import os
import pkgutil
import uuid
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError

import autopager
import scrapy
from arachnado.scheduler.scheduler import Scheduler
from arachnado.utils.misc import add_scheme_if_missing, get_netloc
from autologin_middleware import link_looks_like_logout
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from scrapy.http.response.html import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy_redis.spiders import RedisMixin
from scrapy_splash.request import SplashRequest
from scrapy_splash.response import SplashResponse, SplashTextResponse, SplashJsonResponse
from six.moves.urllib.parse import urljoin, urlparse


class ArachnadoSpider(scrapy.Spider):
    """
    A base spider that contains common attributes and utilities for all
    Arachnado spiders
    """
    crawl_id = None  # unique crawl ID, assigned by DomainCrawlers
    motor_job_id = None  # MongoDB record ID, assigned by MongoExportPipeline
    domain = None  # seed url, set by caller code

    def __init__(self, *args, **kwargs):
        super(ArachnadoSpider, self).__init__(*args, **kwargs)
        # don't log scraped items
        logging.getLogger("scrapy.core.scraper").setLevel(logging.INFO)

    @classmethod
    def inherit_from_me(cls, spider_cls):
        """
        Ensure that spider is inherited from ArachnadoSpider
        to receive its features. HackHackHack.

        >>> class Foo(scrapy.Spider):
        ...     name = 'foo'
        >>> issubclass(Foo, ArachnadoSpider)
        False
        >>> Foo2 = ArachnadoSpider.inherit_from_me(Foo)
        >>> Foo2.name
        'foo'
        >>> issubclass(Foo2, ArachnadoSpider)
        True
        """
        if not isinstance(spider_cls, cls):
            return type(spider_cls.__name__, (spider_cls, cls), {})
        return spider_cls


class CrawlWebsiteSpider(ArachnadoSpider):
    """
    A spider which crawls all the website.
    To run it, set its ``crawl_id`` and ``domain`` arguments.
    """
    name = 'generic'
    custom_settings = {
        'DEPTH_LIMIT': 10,
    }

    def __init__(self, *args, **kwargs):
        super(CrawlWebsiteSpider, self).__init__(*args, **kwargs)
        self.start_url = add_scheme_if_missing(self.domain)

    def start_requests(self):
        self.logger.info("Started job %s (mongo id=%s) for domain %s",
                         self.crawl_id, self.motor_job_id, self.domain)
        yield scrapy.Request(self.start_url, self.parse_first,
                             dont_filter=True)

    def parse_first(self, response):
        # If there is a redirect in the first request, use the target domain
        # to restrict crawl instead of the original.
        self.domain = get_netloc(response.url)
        self.crawler.stats.set_value('arachnado/start_url', self.start_url)
        self.crawler.stats.set_value('arachnado/domain', self.domain)

        allow_domain = self.domain
        if self.domain.startswith("www."):
            allow_domain = allow_domain[len("www."):]

        self.state['allow_domain'] = allow_domain

        yield self._request_info_item(response)

        for elem in self.parse(response):
            yield elem

    @property
    def link_extractor(self):
        return LinkExtractor(
            allow_domains=[self.state['allow_domain']],
            canonicalize=False,
        )

    @property
    def get_links(self):
        return self.link_extractor.extract_links

    def parse(self, response):
        if not isinstance(response, HtmlResponse):
            self.logger.info("non-HTML response is skipped: %s" % response.url)
            return

        yield self._request_info_item(response)

        if self.settings.getbool('PREFER_PAGINATION'):
            # Follow pagination links; pagination is not a subject of
            # a max depth limit. This also prioritizes pagination links because
            # depth is not increased for them.
            with _dont_increase_depth(response):
                for url in self._pagination_urls(response):
                    yield scrapy.Request(url, meta={'is_page': True})
        for link in self.get_links(response):
            if link_looks_like_logout(link):
                continue
            yield scrapy.Request(link.url, self.parse)

    def _request_info_item(self, response):
        keys = ['depth', 'download_latency', 'download_slot',
                'proxy', 'is_page', 'autologin_active']
        return {
            key: response.meta[key] for key in keys
            if key in response.meta
        }

    def _pagination_urls(self, response):
        return [url for url in autopager.urls(response)
                if self.link_extractor.matches(url)]

    def should_drop_request(self, request):
        if 'allow_domain' not in self.state:  # first request
            return
        if not self.link_extractor.matches(request.url):
            return True


class WideCrawlSpider(CrawlWebsiteSpider):
    """
    Basic spider for wide crawling with Spash support
    """
    name = 'wide'
    download_maxsize = 1024 * 1024 * 1
    start_urls = None
    file_feed = None
    link_ext_allow = None
    link_ext_allow_domains = None
    use_splash = False
    splash_script = None
    s3_export_path = None
    s3_key = None
    s3_secret_key = None
    processed_netloc = None
    only_landing_screens = True
    splash_in_parallel = True
    out_file_dir = None
    handle_httpstatus_list = [400, 404, 401, 403, 404, 429, 500, 520, 504, 503]
    start_priority = 1000
    settings = None
    stats = None
    validate_html = True
    # which responses to store
    allowed_statuses = [200, 301, 302, 303, 304, 307, 500]
    reset_depth_new_domain = True
    keep_domain = False

    def __init__(self, *args, **kwargs):
        if not self.settings:
            self.settings = {}
        super(WideCrawlSpider, self).__init__(*args, **kwargs)
        self.start_urls = kwargs.get("start_urls", [])
        self.file_feed = kwargs.get("file_feed", None)
        self.link_ext_allow = kwargs.get("link_ext_allow", "https?:\/\/[^\/]*\.onion")
        self.link_ext_allow_domains = kwargs.get("link_ext_allow_domains", ())
        self.use_splash = kwargs.get("use_splash", False)
        self.only_landing_screens = kwargs.get("only_landing_screens", True)
        self.splash_in_parallel = kwargs.get("splash_in_parallel", True)
        if self.use_splash:
            self.splash_script = pkgutil.get_data("arachnado", "lua/info.lua").decode("utf-8")
            self.processed_netloc = set([])
            self.out_file_num = 0

    def post_init(self):
        self.download_maxsize = self.settings.get("DOWNLOAD_MAXSIZE", self.download_maxsize)
        self.s3_export_path = self.settings.get('PNG_STORAGE_AWS_S3', None)
        if self.s3_export_path:
            self.s3_key = self.settings.get('AWS_STORAGE_KEY', None)
            self.s3_secret_key = self.settings.get('AWS_STORAGE_SECRET_KEY', None)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        obj = super(WideCrawlSpider, cls).from_crawler(crawler, *args, **kwargs)
        obj.settings = crawler.settings
        obj.stats = crawler.stats
        obj.post_init()
        return obj

    def start_requests(self):
        self.logger.info("Started job %s (mongo id=%s)", self.crawl_id, self.motor_job_id)
        req_urls = []
        if self.start_urls:
            req_urls.extend(self.start_urls)
        if self.file_feed:
            with open(self.file_feed, "r") as urls_file:
                for url in urls_file:
                    req_urls.append(url)
        for url in req_urls:
            for req in self.create_request(url, self.parse):
                yield req

    def create_request(self,
                       url,
                       callback,
                       cookies={},
                       add_args={},
                       add_meta={},
                       priority=0,
                       source_url=None
                       ):
        errback = self.process_error
        site_passwords = self.settings.get("SITE_PASSWORDS", {})
        fixed_url = add_scheme_if_missing(url)
        meta = {}
        parsed_url = urlparse(url)
        # dots are replaced for Mongo storage
        url_domain = parsed_url.netloc.replace(".", "_")
        url_ok = True
        if source_url:
            source_domain = urlparse(source_url).netloc
            if self.keep_domain:
                url_ok = source_domain == parsed_url.netloc
            if self.reset_depth_new_domain and source_url:
                if source_domain != parsed_url.netloc:
                    meta["depth"] = 0
        if not url_ok:
            self.logger.debug('Url %s filtered out', url)
            return
        if url_domain in site_passwords:
            meta['autologin_username'] = site_passwords[url_domain].get("username", "")
            meta['autologin_password'] = site_passwords[url_domain].get("password", "")
        meta.update(add_meta)
        if self.use_splash:
            meta.update({"url": fixed_url})
            endpoint = "execute"
            args = {'lua_source': self.splash_script, "cookies": cookies}
            args.update(add_args)
            yield SplashRequest(url=fixed_url,
                                callback=callback,
                                args=args,
                                endpoint=endpoint,
                                dont_filter=True,
                                meta=meta,
                                errback=errback,
                                )
        else:
            yield scrapy.Request(fixed_url, callback, errback=errback, meta=meta, priority=priority)

    def _inc_stats_value(self, stats_name):
        if self.stats:
            self.stats.inc_value(stats_name.replace(" ", "_"), spider=self)

    def process_error(self, failure):
        request = failure.request
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.debug('HttpError on %s', response.url)
            self._inc_stats_value('responses/http error')
        elif failure.check(DNSLookupError):
            self.logger.debug('DNSLookupError on %s', request.url)
            self._inc_stats_value('responses/DNSLookupError')
        elif failure.check(TimeoutError):
            self.logger.debug('TimeoutError on %s', request.url)
            self._inc_stats_value('responses/TimeoutError')

    def parse(self, response):
        is_splash_resp = isinstance(response, SplashResponse) or isinstance(response, SplashTextResponse) \
                         or isinstance(response, SplashJsonResponse)

        if not isinstance(response, HtmlResponse) and not is_splash_resp and not response.meta.get("unusable", False):
            response.meta["unusable"] = True
            response.meta["no_item"] = True
            self.logger.warning("not usable response type skipped: {} from {}".format(type(response), response.url))
            self._inc_stats_value('responses/invalid response type')
            return

        if self.validate_html:
            validation_result = len(response.xpath('.//*')) > 0
            if not validation_result:
                response.meta["no_item"] = True
                self._inc_stats_value('responses/invalid html')
                return

        if self.allowed_statuses:
            if response.status not in self.allowed_statuses:
                response.meta["no_item"] = True
                self._inc_stats_value('responses/invalid http status')
                return

        req_priority = self.start_priority - response.meta["depth"]
        if self.settings.getbool('PREFER_PAGINATION'):
            with _dont_increase_depth(response):
                for url in self._pagination_urls(response):
                    for req in self.create_request(url,
                                                   self.parse,
                                                   add_meta={'is_page': True},
                                                   source_url=response.url):
                        yield req

        for link in self.get_links(response):
            if link_looks_like_logout(link):
                continue
            for req in self.create_request(link.url.replace("\n", ""),
                                           self.parse,
                                           priority=req_priority,
                                           source_url=response.url):
                yield req

        if is_splash_resp:
            if isinstance(response, SplashJsonResponse):
                splash_res = extract_splash_response(response)
                if splash_res:
                    picfilename = "{}.png".format(str(uuid.uuid4()))
                    if self.s3_export_path:
                        s3_store_img(picfilename, self.s3_export_path,
                                     splash_res["png"],
                                     self.s3_key, self.s3_secret_key)
                    if self.s3_export_path:
                        response.meta["pagepicurl"] = picfilename
                        self._inc_stats_value('screenshots/taken')

    @property
    def link_extractor(self):
        return LinkExtractor(
            allow=self.link_ext_allow,
            allow_domains=self.link_ext_allow_domains,
            canonicalize=False,
        )

    def should_drop_request(self, request):
        return False


class RedisWideCrawlSpider(RedisMixin, WideCrawlSpider):
    """
    Spider for wide crawl with Redis requests queue
    """
    name = 'widequeue'

    @classmethod
    def from_crawler(self, crawler, *args, **kwargs):
        obj = super(RedisWideCrawlSpider, self).from_crawler(crawler, *args, **kwargs)
        obj.setup_redis(crawler)
        obj.stats = crawler.stats
        return obj

    def start_requests(self):
        self.logger.info("Started job %s (mongo id=%s)", self.crawl_id, self.motor_job_id)
        req_urls = []
        if self.start_urls:
            req_urls = [x for x in self.start_urls if x != "wide"]
        if self.file_feed:
            with open(self.file_feed, "r") as urls_file:
                for url in urls_file:
                    req_urls.append(url)
        for url in req_urls:
            for req in self.create_request(url, self.parse):
                yield req
        scheduler = Scheduler.from_settings(self.settings)
        scheduler.open(self)
        scheduler.stats = self.stats
        first_req = None
        for req in self.next_requests():
            if not first_req:
                first_req = req
            else:
                scheduler.enqueue_request(req)
        if first_req:
            yield first_req

    def next_requests(self):
        use_set = self.settings.getbool('REDIS_START_URLS_AS_SET')
        fetch_one = self.server.spop if use_set else self.server.lpop
        found = 0
        while found < self.redis_batch_size:
            data = fetch_one(self.redis_key)
            if not data:
                break
            url = data.decode("utf-8")
            reqs = self.create_request(url, self.parse, priority=(self.start_priority + 1))
            if reqs:
                for req in reqs:
                    yield req
                    found += 1
            else:
                self.logger.debug("Request not made from data: %r", data)
        if found:
            self.logger.debug("Read %s requests from '%s'", found, self.redis_key)


class VespinSpider(RedisWideCrawlSpider):
    """
    Experimental spider with combination of site specific crawl and wide crawl
    """
    name = 'vespin'
    # rules for specific domain processing
    site_hints = None
    # rules for links extraction
    site_rules = None

    def __init__(self, *args, **kwargs):
        super(VespinSpider, self).__init__(*args, **kwargs)

    def fix_url(self, url, base_url):
        return urljoin(base_url, url)

    def get_urls(self, sel, xpath, base_url):
        urls = sel.xpath(xpath).extract()
        return [self.fix_url(x, base_url) for x in urls]

    def parse(self, response):
        parsed_url = urlparse(response.url)
        # dots are replaced for Mongo storage
        url_domain = parsed_url.netloc.replace(".", "_")
        rules_found = False
        if self.site_hints:
            site_hint = self.site_hints.get(url_domain, None)
            if site_hint:
                site_key = site_hint["key"]
                site_start_type = site_hint["start_type"]
                page_type = response.meta.get("type", site_start_type)
                response.meta["type"] = page_type
                if self.site_rules:
                    rules_found = True
                    rules = self.site_rules.get(site_key, {}).get(page_type, {})
                    for next_page_type, reqs in rules.items():
                        for req in reqs:
                            urls = self.get_urls(response, req, response.url)
                            for url in urls:
                                for req in self.create_request(url,
                                                               self.parse,
                                                               add_meta={"type": next_page_type},
                                                               source_url=response.url):
                                    yield req
        if not rules_found:
            for res in super(VespinSpider, self).parse(response):
                yield res


@contextlib.contextmanager
def _dont_increase_depth(response):
    # XXX: a hack to keep the same depth for outgoing requests
    response.meta['depth'] -= 1
    try:
        yield
    finally:
        response.meta['depth'] += 1


def extract_splash_response(response):
    if response.status != 200:
        logging.error(response.body)
    else:
        splash_res = response.data
        return splash_res
    return None


def s3_store_img(file_name, bucket_name, img_content, aws_key, aws_secret_key):
    conn = S3Connection(aws_access_key_id=aws_key,
                        aws_secret_access_key=aws_secret_key)
    image_bytes = base64.b64decode(img_content)
    bucket = conn.get_bucket(bucket_name)
    k = Key(bucket)
    k.key = '/img/{}'.format(file_name)
    k.set_contents_from_string(image_bytes)
    k.set_acl('private')
    k.close()


def store_file(file_name, storage_dir, file_content):
    full_path = os.path.join(storage_dir, file_name)
    with open(full_path, "w") as fout:
        fout.write(file_content)
    return full_path


def img_convert(image_splash):
    image_bytes = base64.b64decode(image_splash)
    return image_bytes
