import hashlib
import logging

from arachnado.pipelines.mongoexport import MongoExportPipeline, scrapy_item_to_dict
from arachnado.utils.redis import get_redis_from_settings
from arachnado.utils.twistedtornado import tt_coroutine
from scrapy.utils.python import to_bytes
from tornado import gen
from w3lib.url import canonicalize_url

logger = logging.getLogger(__name__)


class NoDupsExportPipeline(MongoExportPipeline):
    def __init__(self, crawler):
        super(NoDupsExportPipeline, self).__init__(crawler)
        settings = self.crawler.settings
        self.server = get_redis_from_settings(settings)
        self.key = "arachnado_stored_pages"

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    @tt_coroutine
    def process_item(self, item, spider):
        self._update_job_id(spider)
        mongo_item = scrapy_item_to_dict(item)
        if self.job_id_key:
            mongo_item[self.job_id_key] = self.job_id
        try:
            if "url" in mongo_item:
                fixed_url = canonicalize_url(item["url"])
                fp = hashlib.sha1()
                fp.update(to_bytes(fixed_url))
                url_sha = fp.hexdigest()
                added = self.server.sadd(self.key, url_sha)
                seen = added == 0
                self.crawler.stats.inc_value("mongo_export/processed_items")
                if not seen:
                    yield self.items_col.insert(mongo_item)
                    self.crawler.stats.inc_value("mongo_export/items_stored_count")
                else:
                    self.crawler.stats.inc_value("mongo_export/filtered_duplicates")
        except Exception as e:
            self.crawler.stats.inc_value("mongo_export/store_error_count")
            self.crawler.stats.inc_value("mongo_export/store_error_count/" +
                                         e.__class__.__name__)
            logger.error("Error storing item", exc_info=True, extra={
                'crawler': self.crawler
            })
        raise gen.Return(item)

    @tt_coroutine
    def spider_closed(self, spider, reason, **kwargs):
        super(NoDupsExportPipeline, self).spider_closed(spider, reason, **kwargs)
        self.server.delete(self.key)
