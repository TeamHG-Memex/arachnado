# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import datetime
import copy

from tornado import gen
from tornado.ioloop import PeriodicCallback
import elasticsearch as es
from elasticsearch.helpers import bulk
import scrapy
from scrapy.exceptions import NotConfigured
from scrapy import signals

from arachnado.utils.twistedtornado import tt_coroutine


logger = logging.getLogger(__name__)


def scrapy_item_to_dict(son):
    """Recursively convert scrapy.Item to dict"""
    for key, value in list(son.items()):
        if isinstance(value, (scrapy.Item, dict)):
            son[key] = scrapy_item_to_dict(
                son.pop(key)
            )
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, (scrapy.Item, dict)):
                    value[i] = scrapy_item_to_dict(item)
    return dict(son)


class ElasticSearchExportPipeline(object):

    def __init__(self, crawler):
        self.crawler = crawler
        settings = self.crawler.settings
        self.es_export = settings.getbool('ES_EXPORT_ENABLED', False)
        if self.es_export:
            self.job_id_key = settings.get('ES_EXPORT_JOBID_KEY', "job_id")
            self.index_name = settings.get('ES_INDEX_NAME')
            self.type_name = settings.get('ES_TYPE_NAME')
            self.es_url = settings.get('ES_URL')
            self.es_client = es.Elasticsearch([self.es_url])

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    @tt_coroutine
    def process_item(self, item, spider):
        if self.es_export:
            es_item = scrapy_item_to_dict(item)
            es_item["_scrapy_type"] = es_item.pop("_type", None)
            if self.job_id_key:
                es_item[self.job_id_key] = spider.crawl_id
            try:
                index_action = {
                    '_index': self.index_name,
                    '_type': self.type_name,
                    '_source': es_item
                }
                bulk(self.es_client, [index_action])
                self.crawler.stats.inc_value("elasticsearch_export/items_stored_count")
            except Exception as e:
                self.crawler.stats.inc_value("elasticsearch/store_error_count")
                self.crawler.stats.inc_value("elasticsearch/store_error_count/" +
                                             e.__class__.__name__)
                logger.error("Error storing item", exc_info=True, extra={
                    'crawler': self.crawler
                })


