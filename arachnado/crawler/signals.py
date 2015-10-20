# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)


class Signal(object):
    """
    Base signals class to be used by Arachnado Crawler Process.
    """
    def __init__(self, name, supports_defer):
        self.name = name
        self.supports_defer = supports_defer

    def __repr__(self):
        return "%s(%r, supports_defer=%r)" % (
            self.__class__.__name__, self.name, self.supports_defer
        )

SIGNALS = dict(
    engine_started=Signal('engine_started', True),
    engine_stopped=Signal('engine_stopped', True),
    engine_paused=Signal('engine_paused', False),  # custom
    engine_resumed=Signal('engine_resumed', False),  # custom
    engine_tick=Signal('engine_tick', False),  # custom
    spider_opened=Signal('spider_opened', True),
    spider_idle=Signal('spider_idle', False),
    spider_closed=Signal('spider_closed', True),
    spider_closing=Signal('spider_closing', False),  # custom
    spider_error=Signal('spider_error', False),
    request_scheduled=Signal('request_scheduled', False),
    request_dropped=Signal('request_dropped', False),
    response_received=Signal('response_received', False),
    response_downloaded=Signal('response_downloaded', False),
    item_scraped=Signal('item_scraped', True),
    item_dropped=Signal('item_dropped', True),
    downloader_enqueued=Signal('downloader_enqueued', False),
    downloader_dequeued=Signal('downloader_dequeued', False),
    stats_changed=Signal("stats_changed", False),  # custom
)


def get_signal_by_name(cls, signal_name):
    try:
        return SIGNALS[signal_name]
    except KeyError:
        logger.error('No signal named: %s' % signal_name)

locals().update(SIGNALS)
