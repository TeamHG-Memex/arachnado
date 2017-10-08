# -*- coding: utf-8 -*-
"""
Async MongoDB item exporter using Motor_.

.. _Motor: https://github.com/mongodb/motor
"""
from __future__ import absolute_import
import logging
import datetime
import copy
from w3lib.url import canonicalize_url

from tornado import gen
from tornado.ioloop import PeriodicCallback
from bson.objectid import ObjectId
import scrapy
from scrapy.exceptions import NotConfigured
from scrapy import signals

from arachnado.utils.twistedtornado import tt_coroutine
from arachnado.utils.misc import json_encode
from arachnado.utils.mongo import motor_from_uri, replace_dots


logger = logging.getLogger(__name__)


def scrapy_item_to_dict(son):
    """Recursively convert scrapy.Item to dict"""
    for key, value in list(son.items()):
        if isinstance(key, (bytes, bytearray)):
            skey = key.decode("utf8", errors="ignore")
            #son[skey] = value
            son.pop(key)
            son[skey] = value
            key = skey
        if isinstance(value, (scrapy.Item, dict)):
            son[key] = scrapy_item_to_dict(
                son.pop(key)
            )
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, (scrapy.Item, dict)):
                    value[i] = scrapy_item_to_dict(item)
    return dict(son)


class MongoExportPipeline(object):
    """
    This pipeline exports tems to MongoDB using async mongo
    driver (motor). Interaction with MongoDB doesn't block
    the event loop.

    On start it creates object in 'jobs' collection and sets
    spider.motor_job_id to the ID of this job.

    If MONGO_EXPORT_JOBID_KEY option is set, job id is added to
    each stored item under the specified key name.

    If MONGO_EXPORT_DUMP_PERIOD is non-zero then updated job stats are saved
    to Mongo periodically every ``MONGO_EXPORT_DUMP_PERIOD`` seconds
    (default is 60).
    """

    def __init__(self, crawler):
        self.crawler = crawler
        settings = self.crawler.settings
        if not settings.getbool('MONGO_EXPORT_ENABLED', False):
            raise NotConfigured
        self.job_id = None
        self.job_id_key = settings.get('MONGO_EXPORT_JOBID_KEY')
        self.items_uri = settings.get('MONGO_EXPORT_ITEMS_URI')
        self.jobs_uri = settings.get('MONGO_EXPORT_JOBS_URI')
        self.items_client, _, _, _, self.items_col = \
            motor_from_uri(self.items_uri)
        self.jobs_client, _, _, _, self.jobs_col = \
            motor_from_uri(self.jobs_uri)

        # XXX: spider_closed is used instead of close_spider because
        # the latter doesn't provide a closing reason.
        crawler.signals.connect(self.spider_closed, signals.spider_closed)
        crawler.signals.connect(self.spider_closing, signals.spider_closing)

        self.dump_period = settings.getfloat('MONGO_EXPORT_DUMP_PERIOD', 60.0)
        self._dump_pc = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    @classmethod
    def add_url_scheme(cls, url):
        url = url.strip()
        if not url.lower().startswith(("http://", "https://")):
            return "http://{}".format(url)
        return url

    @classmethod
    def get_spider_urls(cls, spider):
        options = getattr(spider.crawler, 'start_options', None)
        urls = None
        if options and "domain" in options:
            urls = [options["domain"]]
        else:
            urls = spider.start_urls
        urls = [cls.add_url_scheme(x) for x in urls]
        return urls

    @tt_coroutine
    def _update_job_id(self, spider):
        if self.job_id:
            return
        else:
            try:
                job_cursor = self.jobs_col.find({'id': spider.crawl_id}).limit(1)
                while (yield job_cursor.fetch_next):
                    job = job_cursor.next_object()
                    self.job_id = str(job['_id'])
                    spider.motor_job_id = str(self.job_id)
                    self.crawler.stats.set_value("mongo_export/mongo_job_id/restored", self.job_id, spider=spider)
                    break
            except Exception:
                logger.error(
                    "Can't update job id.", exc_info=True,
                    extra={'crawler': self.crawler},
                )

    @tt_coroutine
    def open_spider(self, spider):
        try:
            yield self.items_col.ensure_index(self.job_id_key)
            yield self.jobs_col.ensure_index('id', unique=True)
            self._update_job_id(spider)

            job = yield self.jobs_col.find_and_modify({
                'id': spider.crawl_id,
            }, {
                'id': spider.crawl_id,
                'started_at': datetime.datetime.utcnow(),
                'status': 'running',
                'spider': spider.name,
                "urls": self.get_spider_urls(spider),
                'options': getattr(spider.crawler, 'start_options', {}),
            }, upsert=True, new=True)
            self.job_id = str(job['_id'])
            self.crawler.stats.set_value("mongo_export/mongo_job_id/set", self.job_id, spider=spider)
            spider.motor_job_id = str(self.job_id)
            logger.info("Crawl job generated id: %s", self.job_id,
                        extra={'crawler': self.crawler})

            if self.dump_period:
                self._dump_pc = PeriodicCallback(self.dump_stats,
                                                 self.dump_period * 1000)
                self._dump_pc.start()

        except Exception:
            self.job_id = None
            logger.error(
                "Can't connect to %s. Items won't be stored.",
                self.items_uri, exc_info=True,
                extra={'crawler': self.crawler},
            )

    @tt_coroutine
    def spider_closed(self, spider, reason, **kwargs):
        self._update_job_id(spider)
        self._stop_periodic_tasks()

        if self.job_id is None:  # what's this?
            self.jobs_client.close()
            self.items_client.close()
            return

        # update the job one more time because something might
        # have happened while the spider is closing
        yield self._update_finished_job(reason)

        self.jobs_client.close()
        self.items_client.close()
        logger.info("Info is saved for a closed job %s", self.job_id,
                    extra={'crawler': self.crawler})

    @tt_coroutine
    def spider_closing(self, spider, reason, **kwargs):
        self._update_job_id(spider)
        self._stop_periodic_tasks()
        if self.job_id is None:  # what's this?
            return
        yield self._update_finished_job(reason)
        logger.info("Info is saved for a closing job %s", self.job_id,
                    extra={'crawler': self.crawler})

    @tt_coroutine
    def process_item(self, item, spider):
        self._update_job_id(spider)
        mongo_item = scrapy_item_to_dict(item)
        if self.job_id_key:
            mongo_item[self.job_id_key] = self.job_id
        try:
            yield self.items_col.insert(mongo_item)
            self.crawler.stats.inc_value("mongo_export/items_stored_count")
        except Exception as e:
            self.crawler.stats.inc_value("mongo_export/store_error_count")
            self.crawler.stats.inc_value("mongo_export/store_error_count/" +
                                         e.__class__.__name__)
            logger.error("Error storing item", exc_info=True, extra={
                'crawler': self.crawler
            })
        raise gen.Return(item)

    def _update_finished_job(self, reason):
        status = 'finished'
        if reason == 'shutdown':
            status = 'shutdown'
        return self.jobs_col.update(
            {'_id': ObjectId(self.job_id)},
            {'$set': {
                'finished_at': datetime.datetime.utcnow(),
                'status': status,
                'stats': self._get_stats_json(),
                'stats_dict': self._get_stats_escaped(),
            }}
        )

    def _stop_periodic_tasks(self):
        if self._dump_pc is not None and self._dump_pc.is_running():
            self._dump_pc.stop()

    def _get_stats_json(self):
        # json is to fix an issue with dots in key names
        return json_encode(self.crawler.stats.get_stats())

    def _get_stats_escaped(self):
        return replace_dots(copy.deepcopy(self.crawler.stats.get_stats()))

    @gen.coroutine
    def dump_stats(self):
        # json is to fix an issue with dots in key names
        stats = self._get_stats_json()
        yield self.jobs_col.update(
            {'_id': ObjectId(self.job_id)},
            {'$set': {
                'stats': stats,
                'stats_dict': self._get_stats_escaped(),
            }}
        )
        logger.info("Stats are stored for job %s" % self.job_id,
                    extra={'crawler': self.crawler})
