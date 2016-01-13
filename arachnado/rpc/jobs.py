import logging

from tornadorpc import async

class JobsRpc(object):

    logger = logging.getLogger(__name__)

    def __init__(self, handler, job_storage, **kwargs):
        self.handler = handler
        self.storage = job_storage

    @async
    def list(self):
        def _list(future):
            self.handler.result(future.result())
        self.storage.fetch().add_done_callback(_list)

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
        self.handler.write_event('jobs.{}'.format(subscription), data)
