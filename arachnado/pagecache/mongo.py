import pymongo
from scrapy.http import Headers
from scrapy.responsetypes import responsetypes


class MongoCacheStorage(object):
    """A read-only cache storage that uses Arachnado MongoDB for retrieving
    responses"""

    def __init__(self, settings):
        self.db_name = settings.get('MOTOR_PIPELINE_DB_NAME')
        self.db_uri = settings.get('MOTOR_PIPELINE_URI')

    def open_spider(self, spider):
        self.db = pymongo.MongoClient(self.db_uri)
        self.col = self.db[self.db_name]['items']
        self.col.ensure_index('url')

    def close_spider(self, spider):
        self.db.close()

    def retrieve_response(self, spider, request):
        doc = self.col.find_one({'url': request.url})
        if doc is None:
            return  # not cached
        status = 200
        url = doc['url']
        headers = Headers(doc['headers'])
        body = doc['body'].encode('utf-8')
        respcls = responsetypes.from_args(headers=headers, url=url)
        response = respcls(url=url, headers=headers, status=status, body=body)
        return response

    def store_response(self, spider, request, response):
        pass
