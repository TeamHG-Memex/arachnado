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
        if "mongo_id" not in response.meta:
            items = [r for r in result if isinstance(r, scrapy.Item)]
            requests = [r for r in result if isinstance(r, scrapy.Request)]
            page_item = self.get_page_item(response, items)
            return [page_item] + requests
        else:
            return result

    def get_page_item(self, response, items, type_='page'):
        if response.meta.get("no_item", False):
            return
        if response.meta.get("unusable", False):
            page_body = "!REMOVED!"
        else:
            try:
                page_body = response.body_as_unicode()
            except:
                page_body = "!EXTRACTION_ERROR!"

        page_item = {
            'crawled_at': datetime.datetime.utcnow(),
            # TODO: save url in searchable format
            'url': response.url,
            'status': response.status,
            'headers': response.headers.to_unicode_dict(),
            'body': page_body,
            'meta': response.meta,
            'items': items,
            '_type': type_,
        }
        if "pagepicurl" in response.meta:
            page_item["pagepicurl"] = response.meta["pagepicurl"]
        if "url" in response.meta:
            page_item["url"] = response.meta["url"]
        return page_item
