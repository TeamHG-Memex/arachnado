from scrapy.crawler import Crawler
from arachnado.crawler.executionengine import ArachnadoExecutionEngine


class ArachnadoCrawler(Crawler):
    """
    Extended Crawler which uses ArachnadoExecutionEngine.
    """
    def _create_engine(self):
        return ArachnadoExecutionEngine(self, lambda _: self.stop())
