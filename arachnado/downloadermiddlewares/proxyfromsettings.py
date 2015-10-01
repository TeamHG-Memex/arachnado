from scrapy.contrib.downloadermiddleware.httpproxy import HttpProxyMiddleware
from scrapy.exceptions import NotConfigured


class ProxyFromSettingsMiddleware(HttpProxyMiddleware):
    """A middleware that sets proxy from settings file"""

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.proxies = {}
        proxies = [
            ('http', settings.get('HTTP_PROXY')),
            ('https', settings.get('HTTPS_PROXY')),
        ]
        for type_, url in proxies:
            if url:
                self.proxies[type_] = self._get_proxy(url, type_)
        if not self.proxies:
            raise NotConfigured
