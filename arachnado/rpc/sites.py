import logging

from tornadorpc import async


class SitesRpc(object):

    logger = logging.getLogger(__name__)

    def __init__(self, handler, site_storage, **kwargs):
        self.handler = handler
        self.storage = site_storage

    @async
    def list(self):
        def _list(future):
            self.handler.result(future.result())
        self.storage.fetch().add_done_callback(_list)

    def post(self, site):
        self.storage.create(site)

    def patch(self, site):
        self.storage.update(site)

    def delete(self, site):
        self.storage.delete(site)

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
        self.handler.write_event('sites.{}'.format(subscription), data)
