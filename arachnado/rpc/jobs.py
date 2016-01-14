import logging


class JobsRpc(object):

    logger = logging.getLogger(__name__)

    def __init__(self, handler, job_storage, **kwargs):
        self.handler = handler
        self.storage = job_storage

    def subscribe(self, last_id=0, query=None, fields=None):
        self.storage.subscribe('tailed', self._publish, last_id=last_id,
                               query=query, fields=fields)

    def _on_close(self):
        self.storage.unsubscribe('tailed')

    def _publish(self, data):
        if self.storage.tailing:
            self.handler.write_event('jobs.tailed', data)
