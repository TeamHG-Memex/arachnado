import logging
import datetime
from scrapy.extensions.httpcache import DummyPolicy


class CrawledDatePolicy(DummyPolicy):

    def __init__(self, settings):
        super(CrawledDatePolicy, self).__init__(settings)
        self.max_days = settings.get('HTTPCACHE_MAX_DAYS_AGE', 0)

    def is_cached_response_fresh(self, response, request):
        if self.max_days > 0 and "crawled_at" in response.meta:
            try:
                time_diff = datetime.datetime.now() - response.meta["crawled_at"]
                is_fresh = time_diff.days <= self.max_days
                return is_fresh
            except Exception as ex:
                logging.warning("Error while crawled date comparassion" + str(ex))
        return True
