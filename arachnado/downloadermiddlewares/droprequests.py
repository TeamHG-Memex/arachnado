# -*- coding: utf-8 -*-
from __future__ import absolute_import
import warnings

from scrapy.exceptions import IgnoreRequest


class DropRequestsMiddleware:
    """
    Downloader middleware to drop a requests if a certain condition is met.
    It calls ``spider.should_drop_request(request)`` method to check if a
    request should be downloaded or dropped; spider must implement this method.
    """
    def __init__(self, stats):
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        return cls(stats=crawler.stats)

    def process_request(self, request, spider):
        if not hasattr(spider, 'should_drop_request'):
            return
        if not callable(spider.should_drop_request):
            warnings.warn('spider %s has "should_drop_request" attribute, '
                          'but it is not callable' % spider)
            return
        if spider.should_drop_request(request):
            self.stats.inc_value("DropRequestsMiddleware/dropped")
            raise IgnoreRequest()
