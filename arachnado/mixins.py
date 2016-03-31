import logging
import datetime


class ArachnadoSpiderMixin(object):
    """
    An arachnado spider mixin that contains common attributes and utilities for
    all Arachnado spiders
    """
    crawl_id = None
    domain = None
    motor_job_id = None

    def __init__(self, *args, **kwargs):
        super(ArachnadoSpiderMixin, self).__init__(*args, **kwargs)
        # don't log scraped items
        logging.getLogger("scrapy.core.scraper").setLevel(logging.INFO)

    def get_page_item(self, response, type_='page'):
        return {
            'crawled_at': datetime.datetime.utcnow(),
            'url': response.url,
            'status': response.status,
            'headers': response.headers,
            'body': response.body_as_unicode(),
            'meta': response.meta,
            '_type': type_,
        }
