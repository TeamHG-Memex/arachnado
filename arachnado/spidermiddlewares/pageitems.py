from __future__ import absolute_import
import logging
import datetime
import scrapy
from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)


class PageItemsMiddleware(object):

    def __init__(self, crawler):
        if not crawler.settings.getbool('PAGEITEMS_ENABLED', True):
            raise NotConfigured('PAGEITEMS_ENABLED=False')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_spider_output(self, response, result, spider):
        result = list(result)
        items = [r for r in result if isinstance(r, (scrapy.Item, dict))]
        requests = [r for r in result if isinstance(r, scrapy.Request)]
        page_item = self.get_page_item(response, items)
        return [page_item] + requests

    def get_page_item(self, response, items, type_='page'):
        return {
            'crawled_at': datetime.datetime.utcnow(),
            'url': response.url,
            'status': response.status,
            'headers': response.headers.to_unicode_dict(),
            'body': response.body_as_unicode(),
            'items': items,
            '_type': type_,
        }
