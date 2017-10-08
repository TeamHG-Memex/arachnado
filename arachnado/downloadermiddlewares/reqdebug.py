from pprint import pprint
import logging
import json

logger = logging.getLogger(__name__)


class RequestDebugMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        o = cls()
        return o

    def process_request(self, request, spider):
        pprint(request.headers)
        pprint(request.url)
        pprint(request.cookies)
        pprint(request.meta)
        pprint(request.method)
