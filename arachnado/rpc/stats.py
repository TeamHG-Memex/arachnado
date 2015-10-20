import logging


class StatsRpc(object):

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
        for subscription in self.storage.available_subscriptions:
            self.storage.subscribe(
                subscription,
                lambda data, subscription=subscription:
                self._publish(data, subscription)
            )

    def _on_close(self):
        self.storage.unsubscribe(self.storage.available_subscriptions)

    def _publish(self, data, subscription):
        self.handler.write_event('stats.{}'.format(subscription), data)
