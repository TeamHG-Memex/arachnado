import time
import logging
import datetime

from croniter import croniter
from tornado.ioloop import IOLoop

from arachnado.sitechecker import (
    sites_fetched, site_created, site_deleted, site_updated
)


logger = logging.getLogger(__name__)


class Cron(object):

    def __init__(self, crawler_process, site_checker_crawler):
        self.ioloop = IOLoop.instance()
        self.running = False
        self.waiting_calls = {}
        self.crawler_process = crawler_process
        self.site_checker_crawler = site_checker_crawler
        site_signals = site_checker_crawler.site_signals
        site_signals.connect(self.rerun, sites_fetched)
        site_signals.connect(self.rerun, site_created)
        site_signals.connect(self.rerun, site_deleted)
        site_signals.connect(self.rerun, site_updated)

    def start(self):
        self.running = True
        self.rerun()

    def stop(self):
        self.running = False
        self._cancel_all()

    def rerun(self):
        if not self.running:
            return
        deleted_ids = (
            set(self.waiting_calls.keys()) -
            set(self.site_checker_crawler.sites.keys())
        )
        for id_ in self.site_checker_crawler.sites:
            self.schedule(id_)
        for id_ in deleted_ids:
            self.cancel(id_)

    def schedule(self, id_):
        site = self.site_checker_crawler.sites[id_]
        if id_ in self.waiting_calls:
            call, schedule = self.waiting_calls[id_]
            if schedule != site['schedule']:
                self.cancel(id_)
                self.schedule(id_)
            return
        try:
            cron = croniter(site['schedule'])
        except:
            if site.get('schedule_valid', True) is True:
                self.site_checker_crawler.storage.update(
                    {'_id': id_, 'schedule_valid': False}
                )
            logger.warning('CRON entry "{}" invalid for site {}'
                           .format(site['schedule'], site['url']))
        else:
            deadline = cron.get_next()
            delay = deadline - time.time()
            logger.debug('Scheduling {} in {} seconds'
                         .format(site['url'], delay))
            call = self.ioloop.add_timeout(deadline,
                                           self.start_crawl, id_=id_)
            self.waiting_calls[id_] = call, site['schedule']
            self.site_checker_crawler.storage.update({
                '_id': id_,
                'schedule_valid': True,
                'schedule_at': datetime.datetime.fromtimestamp(deadline),
            })

    def cancel(self, id_):
        call, _ = self.waiting_calls[id_]
        self.ioloop.remove_timeout(call)
        self.waiting_calls.pop(id_)

    def cancel_all(self):
        for id_ in self.waiting_calls:
            self.cancel[id_]

    def start_crawl(self, id_):
        self.cancel(id_)
        site = self.site_checker_crawler.sites[id_]
        if not site.get('engine'):
            site['engine'] = 'generic'
        if site['engine'] == 'generic':
            url = site['url']
            args = {}
        else:
            url = 'spider://' + site['engine']
            args = {'post_days': '-1'}  # TODO: change in bot_engines
        self.crawler_process.start_crawl(
            url, {}, args
        )
        self.schedule(id_)
