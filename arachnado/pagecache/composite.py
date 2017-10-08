import logging

import pymongo
from scrapy.http import Headers
from scrapy.responsetypes import responsetypes
from scrapy_splash.responsetypes import responsetypes as splash_responsetypes
from w3lib.url import canonicalize_url

logger = logging.getLogger(__name__)


class CompositeCacheStorage(object):
    def __init__(self, settings):
        self.temp_collection_used = 0
        self.perm_collection_used = 0
        self.temp_collection_errors = 0
        self.perm_collection_errors = 0
        self.db_name = settings.get('MOTOR_PIPELINE_DB_NAME', 'arachnado')
        self.db_uri = settings.get('MOTOR_PIPELINE_URI')
        usable_codes_key = "USABLE_CACHED_RESPONSE_CODES"
        if usable_codes_key in settings:
            self.status_codes = settings[usable_codes_key]
        else:
            self.status_codes = ['200', '203', '301', '302', '303', '307']
        logger.debug("Composite cache storage initiated")

    def open_spider(self, spider):
        self.db = pymongo.MongoClient(self.db_uri)
        self.col = self.db[self.db_name]['items']
        self.pages_col = self.db[self.db_name]['pages']
        self.page_texts_col = self.db[self.db_name]['page_texts']

    def close_spider(self, spider):
        self.db.close()

    def retrieve_response(self, spider, request):
        if 'splash' in request.meta:
            search_url = request.meta.get("url", None)
        else:
            search_url = request.url
        if not search_url:
            return
        search_url2 = canonicalize_url(search_url)
        url_query = {"$or": [{"url": search_url}, {"url": search_url2}]}
        # permanent collection search
        try:
            doc = self.pages_col.find_one(url_query)
            if doc:
                page_body = self.page_texts_col.find_one({"_id": doc["body_id"]})
                if page_body:
                    doc["body"] = page_body["body"]
                    logger.debug("{} found at pages collection".format(search_url))
                    self.perm_collection_used += 1
                else:
                    doc = None
        except Exception:
            logger.exception("perm cache error")
            doc = None
            self.perm_collection_errors += 1
        if doc is None:
            # temp collection search
            try:
                doc = self.col.find_one(url_query)
                logger.debug("{} found at temp collection".format(search_url))
                self.temp_collection_used += 1
            except Exception:
                logger.exception("temp cache error")
                self.temp_collection_errors += 1
        if doc is None:
            logger.debug("{} not found".format(search_url))
            return
        status = str(doc.get("status", -1))
        if status not in self.status_codes:
            return
        url = doc['url']
        headers = Headers(doc['headers'])
        body = doc['body'].encode('utf-8')
        if 'splash' in request.meta:
            respcls = splash_responsetypes.from_args(headers=headers, url=url)
        else:
            respcls = responsetypes.from_args(headers=headers, url=url)
        logger.debug("{}, body len {}".format(url, len(body)))
        if "es_id" in doc and not len(body) and self.es_client:
            logger.debug("elasticsearch as datasource")
            es_data = self.es_client.get(index=self.index_name, doc_type=self.type_name, id=doc["es_id"])
            body = es_data["_source"][self.es_page_body].encode('utf8', errors='ignore')
        response = respcls(url=url, headers=headers, status=status, body=body, request=request)
        response.meta["mongo_id"] = doc["_id"]
        response.meta["crawled_at"] = doc.get("crawled_at", None)
        logger.debug("{}, body len {}".format(url, len(body)))
        return response

    def store_response(self, spider, request, response):
        # implemented at mongoexport pipeline
        pass
