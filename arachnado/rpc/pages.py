class PagesRpc(object):

    def __init__(self, handler, page_storage, **kwargs):
        self.handler = handler
        self.storage = page_storage

    def subscribe(self, last_id=0, query=None, fields=None):
        self.storage.subscribe('tailed', self._publish, last_id=last_id,
                               query=query, fields=fields)

    def _on_close(self):
        self.storage.unsubscribe('tailed')

    def _publish(self, data):
        if self.storage.tailing:
            self.handler.write_event('pages.tailed', data)
