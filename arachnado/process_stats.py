# -*- coding: utf-8 -*-
""" Process monitor: CPU, RAM """
from __future__ import absolute_import
import os
import logging

import psutil
from tornado.ioloop import PeriodicCallback
from scrapy.signalmanager import SignalManager


logger = logging.getLogger(__name__)


class ProcessStatsMonitor(object):
    """ A class which emits process stats periodically """

    signal_updated = object()

    def __init__(self, interval=2.0):
        self.signals = SignalManager(self)
        self.process = psutil.Process(os.getpid())
        self.interval = interval
        self._task = PeriodicCallback(self._emit, self.interval*1000)
        self._recent = {}

    def start(self):
        self._task.start()

    def stop(self):
        self._task.stop()

    def get_recent(self):
        return self._recent

    def _emit(self):
        stats = {
            'cpu_percent': self.process.cpu_percent(),
            'ram_percent': self.process.memory_percent(),
        }
        self._recent = stats
        # logger.debug("process stats: %s", stats)
        self.signals.send_catch_log(self.signal_updated, stats=stats)
