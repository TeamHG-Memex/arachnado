import logging


class Stats(object):

    logger = logging.getLogger(__name__)

    def __init__(self, handler, stats_storage, **kwargs):
        self.handler = handler
        self.storage = stats_storage

    def list(self):
        return self.storage.cache.values()

    def post(self, site):
        self.storage.create(site)

    def patch(self, site):
        self.storage.update(site)

    def subscribe(self):
        for event_name in self.storage.available_events:
            self.storage.subscribe(
                event_name,
                partial(self._publish, event=event_name)
            )

    def _on_close(self):
        self.storage.unsubscribe(self.storage.available_events)

    def _publish(self, event, data):
        self.handler.write_event('stats.{}'.format(event), data)
