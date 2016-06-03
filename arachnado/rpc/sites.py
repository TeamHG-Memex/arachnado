import logging


class Sites(object):

    logger = logging.getLogger(__name__)

    def __init__(self, handler, site_storage, **kwargs):
        self.handler = handler
        self.storage = site_storage

    def list(self):
        return self.storage.fetch()

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

    # TODO - call it!
    def _on_close(self):
        self.storage.unsubscribe(self.storage.available_subscriptions)

    def _publish(self, data, subscription):
        self.handler.write_event('sites.{}'.format(subscription), data)
