import logging

from arachnado.storages.mongotail import MongoTailStorage


class MongoTailStorageWrapper(object):
    """
    This object is exposed for RPC requests.
    It allows to subscribe for scraping job or pages updates.
    """
    handler_id = None
    callback_meta = None
    callback = None
    logger = logging.getLogger(__name__)
    storage_param_name = ""

    def __init__(self, handler, **kwargs):
        self.handler = handler
        self.storage = MongoTailStorage(kwargs['objects_uri'][self.storage_param_name], cache=True)

    def subscribe(self, last_id=0, query=None, fields=None):
        """ Subscribe for updates. """
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
