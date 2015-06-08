# -*- coding: utf-8 -*-
"""
CrawlerProcessSignals class.
"""
from __future__ import absolute_import
from scrapy import signals


SIGNAL_NAMES = [
    'engine_started',
    'engine_stopped',
    'item_scraped',
    'item_dropped',
    'spider_closed',
    'spider_opened',
    'spider_idle',
    'spider_error',
    'request_scheduled',
    'request_dropped',
    'response_received',
    'response_downloaded',
]


class _Signal(object):
    def __init__(self, name, supports_defer):
        self.name = name
        self.supports_defer = supports_defer

    def __repr__(self):
        return "%s(%r, supports_defer=%r)" % (
            self.__class__.__name__, self.name, self.supports_defer
        )


def _get_crawler_process_signals_cls():
    spider_to_cp = {}

    class CrawlerProcessSignals(object):
        @classmethod
        def signal(cls, spider_signal):
            return spider_to_cp[spider_signal]

        engine_started = _Signal('engine_started', True)
        engine_stopped = _Signal('engine_stopped', True)
        spider_opened = _Signal('spider_opened', True)
        spider_idle = _Signal('spider_idle', False)
        spider_closed = _Signal('spider_closed', True)
        spider_error = _Signal('spider_error', False)
        request_scheduled = _Signal('request_scheduled', False)
        request_dropped = _Signal('request_dropped', False)
        response_received = _Signal('response_received', False)
        response_downloaded = _Signal('response_downloaded', False)
        item_scraped = _Signal('item_scraped', True)
        item_dropped = _Signal('item_dropped', True)

    for name in SIGNAL_NAMES:
        signal = getattr(signals, name)
        cp_signal = getattr(CrawlerProcessSignals, name)
        spider_to_cp[signal] = cp_signal

    return CrawlerProcessSignals


CrawlerProcessSignals = _get_crawler_process_signals_cls()
