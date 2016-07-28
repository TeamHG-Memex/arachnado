import logging

from arachnado.storages.mongotail import MongoTailStorage


class Jobs(object):
    """
    This object is exposed for RPC requests.
    It allows to subscribe for scraping job updates.
    """
    callback_meta = None
    callback = None
    logger = logging.getLogger(__name__)

    def __init__(self, handler, job_storage, **kwargs):
        self.handler = handler
        self.storage = job_storage  # type: MongoTailStorage

    def subscribe(self, last_id=0, query=None, fields=None):
        """ Subscribe for job updates. """
        self.storage.subscribe('tailed', self._publish, last_id=last_id,
                               query=query, fields=fields)

    def _on_close(self):
        self.storage.unsubscribe('tailed')

    def _publish(self, data):
        if self.callback:
            _callback = self.callback
        else:
            _callback = self.handler.write_event
        if self.storage.tailing:
            if self.callback_meta:
                _callback(data, callback_meta=self.callback_meta)
            else:
                _callback(data)
