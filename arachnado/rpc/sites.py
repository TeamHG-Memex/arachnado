import logging
from functools import partial

from arachnado.storages.mongotail import MongoTailStorage


class Sites(object):
    """ 'Known sites' object exposed via JSON-RPC """
    logger = logging.getLogger(__name__)

    def __init__(self, handler, site_storage, **kwargs):
        self.handler = handler
        self.storage = site_storage  # type: MongoTailStorage

    def list(self):
        return self.storage.fetch()

    def post(self, site):
        self.storage.create(site)

    def patch(self, site):
        self.storage.update(site)

    def delete(self, site):
        self.storage.delete(site)

    def subscribe(self):
        for event_name in self.storage.available_events:
            self.storage.subscribe(
                event_name,
                partial(self._publish, event=event_name)
            )

    def _on_close(self):
        self.storage.unsubscribe(self.storage.available_events)

    def _publish(self, event, data):
        self.handler.write_event('sites.{}'.format(event), data)
