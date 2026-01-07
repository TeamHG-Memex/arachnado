import time
import logging
import datetime

from croniter import croniter
from tornado.ioloop import IOLoop


logger = logging.getLogger(__name__)


class Cron(object):

    def __init__(self, domain_crawlers, site_storage):
        self.ioloop = IOLoop.instance()
        self.running = False
        self.waiting_calls = {}
        self.domain_crawlers = domain_crawlers
        self.site_storage = site_storage
        self.site_storage.subscribe(self.site_storage.available_events,
                                    self.rerun)

    def start(self):
        self.running = True
        self.rerun()

    def stop(self):
        self.running = False
        self.cancel_all()

    def rerun(self):
        if not self.running:
            return
        deleted_ids = (
            set(self.waiting_calls.keys()) -
            set(self.site_storage.cache.keys())
        )
        for id_ in self.site_storage.cache:
            self.schedule(id_)
        for id_ in deleted_ids:
            self.cancel(id_)

    def schedule(self, id_):
        site = self.site_storage.cache[id_]
        if 'schedule' not in site:
            return
        if id_ in self.waiting_calls:
            call, schedule = self.waiting_calls[id_]
            if schedule != site['schedule']:
                self.cancel(id_)
                self.schedule(id_)
            return

        if not site['schedule']:
            return

        try:
            cron = croniter(site['schedule'])
        except Exception:
            if site.get('schedule_valid', True) is True:
                self.site_storage.update(
                    {'_id': id_, 'schedule_valid': False}
                )
            logger.warning('CRON entry "{}" invalid for site {}'
                           .format(site['schedule'], site['url']))
        else:
            deadline = cron.get_next()
            delay = deadline - time.time()
            logger.debug('Scheduling {} in {:.1f} seconds'
                         .format(site['url'], delay))
            call = self.ioloop.add_timeout(deadline,
                                           self.start_crawl, id_=id_)
            self.waiting_calls[id_] = call, site['schedule']
            self.site_storage.update({
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
            self.cancel(id_)

    def start_crawl(self, id_):
        self.cancel(id_)
        try:
            site = self.site_storage.cache[id_]
        except KeyError:
            return

        args = _key_value_to_dict(site.get('args', []))
        settings = _key_value_to_dict(site.get('settings', []))

        # checking for == 'generic' to be backwards compatible
        if not site.get('engine') or site['engine'] == 'generic':
            url = site['url']
        else:
            url = 'spider://' + site['engine']
            args.setdefault('post_days', '-1')  # TODO: move it to bot_engines?

        crawler = self.domain_crawlers.start(url, args, settings)
        if crawler:
            self.schedule(id_)


def _key_value_to_dict(obj):
    if isinstance(obj, dict):
        return obj
    return {el['key']: el['value'] for el in obj}
