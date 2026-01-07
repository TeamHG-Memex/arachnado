# -*- coding: utf-8 -*-
from __future__ import absolute_import
import contextlib
import logging

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http.response.html import HtmlResponse
from autologin_middleware import link_looks_like_logout

from arachnado.utils.misc import add_scheme_if_missing, get_netloc


class ArachnadoSpider(scrapy.Spider):
    """
    A base spider that contains common attributes and utilities for all
    Arachnado spiders
    """
    crawl_id = None       # unique crawl ID, assigned by DomainCrawlers
    motor_job_id = None   # MongoDB record ID, assigned by MongoExportPipeline
    domain = None         # seed url, set by caller code

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
        import autopager
        return [url for url in autopager.urls(response)
                if self.link_extractor.matches(url)]

    def should_drop_request(self, request):
        if 'allow_domain' not in self.state:  # first request
            return
        if not self.link_extractor.matches(request.url):
            return True


@contextlib.contextmanager
def _dont_increase_depth(response):
    # XXX: a hack to keep the same depth for outgoing requests
    response.meta['depth'] -= 1
    try:
        yield
    finally:
        response.meta['depth'] += 1
