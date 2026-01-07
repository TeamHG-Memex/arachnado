# -*- coding: utf-8 -*-
""" Process monitor: CPU, RAM """
from __future__ import absolute_import
import os
import time
import logging

# import yappi
import psutil
from tornado.ioloop import PeriodicCallback
from scrapy.signalmanager import SignalManager

logger = logging.getLogger(__name__)


class ProcessStatsMonitor(object):
    """ A class which emits process stats periodically """

    signal_updated = object()

    def __init__(self, interval=1.0):
        self.signals = SignalManager(self)
        self.process = psutil.Process(os.getpid())
        self.interval = interval
        self._task = PeriodicCallback(self._emit, self.interval*1000)
        self._recent = {}

    def start(self):
        # yappi.start()
        self._task.start()

    def stop(self):
        self._task.stop()
        # stats = yappi.get_func_stats()
        # stats.sort('tsub', 'desc')
        # with open("func-stats.txt", 'wt') as f:
        #     stats.print_all(f, columns={
        #         0: ("name", 80),
        #         1: ("ncall", 10),
        #         2: ("tsub", 8),
        #         3: ("ttot", 8),
        #         4: ("tavg",8)
        #     })
        #
        # pstats = yappi.convert2pstats(stats)
        # pstats.dump_stats("func-stats.prof")

    def get_recent(self):
        return self._recent

    def _emit(self):
        cpu_times = self.process.cpu_times()
        ram_usage = self.process.memory_info()
        stats = {
            'ram_percent': self.process.memory_percent(),
            'ram_rss': ram_usage.rss,
            'ram_vms': ram_usage.vms,
            'cpu_percent': self.process.cpu_percent(),
            'cpu_time_user': cpu_times.user,
            'cpu_time_system': cpu_times.system,
            'num_fds': self.process.num_fds(),
            'context_switches': self.process.num_ctx_switches(),
            'num_threads': self.process.num_threads(),
            'server_time': int(time.time()*1000),
        }
        self._recent = stats
        self.signals.send_catch_log(self.signal_updated, stats=stats)
