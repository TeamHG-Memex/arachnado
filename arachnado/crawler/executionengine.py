from scrapy.utils.reactor import CallLaterOnce
from scrapy.core.engine import ExecutionEngine

from arachnado.crawler.signals import SIGNALS


class ArachnadoExecutionEngine(ExecutionEngine):
    """
    Extended ExecutionEngine.
    It sends a signal when engine gets scheduled to stop.
    """
    def __init__(self, *args, **kwargs):
        super(ArachnadoExecutionEngine, self).__init__(*args, **kwargs)
        self.send_tick = CallLaterOnce(self._send_tick_signal)

    def close_spider(self, spider, reason='cancelled'):
        if self.slot.closing:
            return self.slot.closing
        self.crawler.crawling = False
        self.signals.send_catch_log(SIGNALS['spider_closing'])
        return super(ArachnadoExecutionEngine, self).close_spider(spider,
                                                                  reason)

    def pause(self):
        """Pause the execution engine"""
        super(ArachnadoExecutionEngine, self).pause()
        self.signals.send_catch_log(SIGNALS['engine_paused'])

    def unpause(self):
        """Resume the execution engine"""
        super(ArachnadoExecutionEngine, self).unpause()
        self.signals.send_catch_log(SIGNALS['engine_resumed'])

    def _next_request(self, spider):
        res = super(ArachnadoExecutionEngine, self)._next_request(spider)
        self.send_tick.schedule(0.1)  # avoid sending the signal too often
        return res

    def _send_tick_signal(self):
        self.signals.send_catch_log_deferred(SIGNALS['engine_tick'])
