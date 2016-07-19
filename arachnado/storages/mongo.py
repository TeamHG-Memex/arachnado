from copy import deepcopy
from collections import defaultdict

from tornado.gen import coroutine, Return
from bson.objectid import ObjectId
from scrapy.signalmanager import SignalManager

from arachnado.utils.mongo import motor_from_uri, replace_dots


class MongoStorage(object):
    """
    Utility class for working with MongoDB data.
    It supports CRUD operations and allows to subscribe to
    created/updated/deleted events.
    """
    def __init__(self, mongo_uri, cache=False):
        self.mongo_uri = mongo_uri
        _, _, _, _, self.col = motor_from_uri(mongo_uri)
        self.signal_manager = SignalManager()
        # Used for unsubscribe
        # disconnect() requires reference to original callback
        self._callbacks = {}
        self.fetching = False
        self.signals = {
            'created': object(),
            'updated': object(),
            'deleted': object(),
        }
        # XXX: cache is used in arachnado.cron and arachnado.site_checker.
        # Is it needed?
        self.cache_flag = cache
        if cache:
            self.cache = defaultdict(dict)
        else:
            self.cache = None

    def subscribe(self, events=None, callback=None):
        if events is None:
            events = self.available_events
        if not isinstance(events, list):
            events = [events]
        for event_name in events:
            if event_name not in self.signals:
                raise ValueError('Invalid event name: {}'.format(event_name))
            self.signal_manager.connect(callback,
                                        self.signals[event_name],
                                        weak=False)
            self._callbacks[event_name] = callback

    def unsubscribe(self, events=None):
        if events is None:
            events = self.available_events
        if not isinstance(events, list):
            events = [events]
        for event_name in events:
            try:
                self.signal_manager.disconnect(
                    self._callbacks[event_name],
                    self.signals[event_name],
                    weak=False
                )
                self._callbacks.pop(event_name, None)
            except KeyError:
                # FIXME: when can it happen?
                pass

    @property
    def available_events(self):
        return list(self.signals.keys())

    @coroutine
    def fetch(self, query=None):
        if self.fetching:
            return
        self.fetching = True
        docs = []
        cursor = self.col.find(query)
        while (yield cursor.fetch_next):
            doc = cursor.next_object()
            docs.append(doc)
            #if self.cache is not None:
            #    self.cache[str(doc['_id'])] = doc
            #    if str(doc['_id']) not in self.cache:
            #        self.signal_manager.send_catch_log(
            #            self.signals['created'], data=doc
            #        )
        self.fetching = False
        raise Return(docs)

    @coroutine
    def create(self, doc):
        doc = replace_dots(doc)
        result = yield self.col.insert(doc)
        if self.cache is not None:
            self.cache[str(doc['_id'])] = doc
        self.signal_manager.send_catch_log(self.signals['created'], data=doc)
        raise Return(result)

    @coroutine
    def ensure_index(self, key_or_list):
        result = yield self.col.ensure_index(key_or_list)
        raise Return(result)

    @coroutine
    def update(self, doc):
        doc = replace_dots(doc)
        doc_copy = deepcopy(doc)
        doc_copy.pop('_id')
        result = yield self.col.update({
            '_id': ObjectId(doc['_id'])
        }, {
            '$set': doc_copy
        })
        if self.cache is not None:
            self.cache[str(doc['_id'])].update(doc)
        self.signal_manager.send_catch_log(self.signals['updated'], data=doc)
        raise Return(result)

    @coroutine
    def delete(self, doc):
        result = yield self.col.remove({'_id': ObjectId(doc['_id'])})
        if self.cache is not None:
            self.cache.pop(str(doc['_id']), None)
        self.signal_manager.send_catch_log(self.signals['deleted'], data=doc)
        raise Return(result)
