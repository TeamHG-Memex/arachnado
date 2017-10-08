import pymongo
from scrapy.http import Headers
from scrapy.responsetypes import responsetypes
from scrapy_splash import SplashResponse
from six.moves.urllib.parse import urlparse, urlunparse, ParseResult


class MongoCacheStorage(object):
    """A read-only cache storage that uses Arachnado MongoDB for retrieving
    responses"""

    def __init__(self, settings):
        self.db_name = settings.get('MOTOR_PIPELINE_DB_NAME', 'arachnado')
        self.db_uri = settings.get('MOTOR_PIPELINE_URI')
        usable_codes_key = "USABLE_CACHED_RESPONSE_CODES"
        if usable_codes_key in settings:
            self.status_codes = settings[usable_codes_key]
        else:
            self.status_codes = ['200', '203', '301', '302', '303', '307']

    def open_spider(self, spider):
        self.db = pymongo.MongoClient(self.db_uri)
        self.col = self.db[self.db_name]['items']
        self.col.ensure_index('url')

    def close_spider(self, spider):
        self.db.close()

    def retrieve_response(self, spider, request):
        if 'splash' in request.meta:
            doc_url = request.meta.get("url", None)
        else:
            doc_url = request.url
        if not doc_url:
            return
        doc = self.col.find_one({'url': doc_url})
        if doc is None:
            url_obj = urlparse(doc_url)
            url_obj2 = ParseResult(url_obj.scheme, url_obj.netloc, url_obj.path, url_obj.params, url_obj.query, '')
            search_url = urlunparse(url_obj2)
            # TODO: remove site specific session id, etc.
            doc = self.col.find_one({'url': search_url})
        if doc is None:
            return
        status = str(doc.get("status", -1))
        if status not in self.status_codes:
            return
        url = doc['url']
        headers = Headers(doc['headers'])
        body = doc['body'].encode('utf-8')
        if 'splash' in request.meta:
            respcls = SplashResponse
        else:
            respcls = responsetypes.from_args(headers=headers, url=url)
        response = respcls(url=url, headers=headers, status=status, body=body, request=request)
        response.meta["mongo_id"] = doc["_id"]
        response.meta["crawled_at"] = doc.get("crawled_at", None)
        return response

    def store_response(self, spider, request, response):
        # implemented at mongoexport pipeline
        pass
