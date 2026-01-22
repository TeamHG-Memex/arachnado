# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import time
from tornado.ioloop import PeriodicCallback, IOLoop

from arachnado.crawler_process import (
    ArachnadoCrawlerProcess,
    agg_stats_changed,
    CrawlerProcessSignals as CPS,
)
from arachnado.process_stats import ProcessStatsMonitor
from arachnado.wsbase import BaseWSHandler


logger = logging.getLogger(__name__)

#
# class Broker(object):
#     """ Pub/Sub broker """
#     def __init__(self):
#         self.subscribers = defaultdict(set)
#
#     def on(self, event, callback):
#         self.subscribers[event].add(callback)
#
#     def off(self, event, callback):
#         self.subscribers[event].remove(callback)
#
#     def emit(self, event, message):
#         for cb in self.subscribers[event]:
#             cb(message)
#
#
# class WSUpdatesHandler(BaseWSHandler):
#     """ WebSocket handler which sends updates to the client """
#
#     def initialize(self, broker):
#         self.broker = broker
#
#     def on_open(self, *args, **kwargs):
#         pass
#


class Monitor(BaseWSHandler):
    """
    WebSocket handler which pushes CrawlerProcess events to a client.
    """
    engine_signals = [
        CPS.spider_closing, CPS.engine_paused, CPS.engine_resumed,
        CPS.engine_tick, CPS.downloader_enqueued, CPS.downloader_dequeued
    ]

    def initialize(self, crawler_process, opts, **kwargs):
        """
        :param ArachnadoCrawlerProcess crawler_process: crawler process
        """
        self.cp = crawler_process
        self.opts = opts
        self._jobs_state_pending = False
        self._last_jobs_state_time = 0
        self._jobs_state_throttle_ms = 500  # throttle to max 2 updates per second

    def on_open(self):
        logger.debug("new connection")
        self.cp.signals.connect(self.on_stats_changed, agg_stats_changed)
        self.cp.signals.connect(self.on_spider_opened, CPS.spider_opened)
        self.cp.signals.connect(self.on_spider_closed, CPS.spider_closed)

        for signal in self.engine_signals:
            self.cp.signals.connect(self.on_engine_state_changed, signal)

        self.cp.procmon.signals.connect(self.on_process_stats, ProcessStatsMonitor.signal_updated)
        self.write_event("jobs:state", self.cp.jobs)

    def on_close(self):
        logger.debug("connection closed")
        self.cp.signals.disconnect(self.on_stats_changed, agg_stats_changed)
        self.cp.signals.disconnect(self.on_spider_opened, CPS.spider_opened)
        self.cp.signals.disconnect(self.on_spider_closed, CPS.spider_closed)
        for signal in self.engine_signals:
            self.cp.signals.disconnect(self.on_engine_state_changed, signal)
        self.cp.procmon.signals.disconnect(self.on_process_stats, ProcessStatsMonitor.signal_updated)

    def on_spider_opened(self, spider):
        self._send_jobs_state_immediate()

    def on_spider_closed(self, spider, reason):
        self._send_jobs_state_immediate()

    def on_engine_state_changed(self, crawler):
        self._send_jobs_state_throttled()

    def on_tick(self):
        self._send_jobs_state_throttled()

    def on_stats_changed(self, changes, crawler):
        # Don't log anything here! Log events are counted by stats collector,
        # so logging a message will trigger more on_stats_changed events.
        crawl_id = crawler.spider.crawl_id
        self.write_event("stats:changed", [crawl_id, changes])

    def on_process_stats(self, stats):
        self.write_event("process:stats", stats)

    def _send_jobs_state_immediate(self):
        """Send jobs state immediately without throttling."""
        self._jobs_state_pending = False
        self._last_jobs_state_time = time.time() * 1000
        self.write_event("jobs:state", self.cp.jobs)

    def _send_jobs_state_throttled(self):
        """
        Send jobs state with throttling to avoid overwhelming the client.
        Updates are limited to once per _jobs_state_throttle_ms milliseconds.
        """
        current_time = time.time() * 1000
        time_since_last = current_time - self._last_jobs_state_time

        if time_since_last >= self._jobs_state_throttle_ms:
            # Enough time has passed, send immediately
            self._send_jobs_state_immediate()
        elif not self._jobs_state_pending:
            # Schedule a delayed update
            self._jobs_state_pending = True
            delay = (self._jobs_state_throttle_ms - time_since_last) / 1000.0
            IOLoop.current().call_later(delay, self._send_pending_jobs_state)

    def _send_pending_jobs_state(self):
        """Send pending jobs state update."""
        if self._jobs_state_pending:
            self._send_jobs_state_immediate()

    def _send_jobs_state(self):
        """Deprecated: use _send_jobs_state_throttled or _send_jobs_state_immediate."""
        self._send_jobs_state_throttled()
