from copy import deepcopy
from collections import defaultdict

from tornado.gen import coroutine, Return
from bson.objectid import ObjectId
from scrapy.signalmanager import SignalManager

from arachnado.utils.mongo import motor_from_uri


def replace_dots(son):
    """Recursively replace keys that contains dots"""
    for key, value in son.items():
        if '.' in key:
            new_key = key.replace('.', '_')
            if isinstance(value, dict):
                son[new_key] = replace_dots(
                    son.pop(key)
                )
            else:
                son[new_key] = son.pop(key)
        elif isinstance(value, dict):  # recurse into sub-docs
            son[key] = replace_dots(value)
    return son


class MongoStorage(object):

    def __init__(self, mongo_uri, cache=False):
        self.mongo_uri = mongo_uri
        self.cache_flag = cache
        _, _, _, _, self.col = motor_from_uri(mongo_uri)
        self.signal_manager = SignalManager()
        # Used for unsubscribe
        # disconnect() requires reference to original callback
        self.subscription_callbacks = {}
        if cache:
            self.cache = defaultdict(dict)
        else:
            self.cache = None
        self.fetching = False
        self.signals = {
            'created': object(),
            'updated': object(),
            'deleted': object(),
        }

    def subscribe(self, subscriptions=None, callback=None):
        if subscriptions is None:
            subscriptions = self.available_subscriptions
        if not isinstance(subscriptions, list):
            subscriptions = [subscriptions]
        for subscription in subscriptions:
            try:
                self.signal_manager.connect(callback,
                                            self.signals[subscription],
                                            weak=False)
                self.subscription_callbacks[subscription] = callback
            except KeyError as exc:
                raise ValueError('Invalid subscription type: {}'.format(exc))

    def unsubscribe(self, subscriptions=None):
        if subscriptions is None:
            subscriptions = self.available_subscriptions
        if not isinstance(subscriptions, list):
            subscriptions = [subscriptions]
        for subscription in subscriptions:
            try:
                self.signal_manager.disconnect(
                    self.subscription_callbacks[subscription],
                    self.signals[subscription],
                    weak=False
                )
                self.subscription_callbacks.pop(subscription, None)
            except KeyError:
                pass

    @property
    def available_subscriptions(self):
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
