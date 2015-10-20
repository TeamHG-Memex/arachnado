import pymongo
from bson.objectid import ObjectId
from tornado.gen import sleep, coroutine

from arachnado.storages.mongo import MongoStorage


class MongoTailStorage(MongoStorage):

    def __init__(self, *args, **kwargs):
        super(MongoTailStorage, self).__init__(*args, **kwargs)
        self.tailing = False
        self.signals['tailed'] = object()

    def subscribe(self, subscriptions, callback, last_id=None, query=None,
                  fields=None):
        if 'tailed' in subscriptions:
            self.tail(query, fields, last_id)
        super(MongoTailStorage, self).subscribe(subscriptions, callback)

    def unsubscribe(self, subscriptions):
        if 'tailed' in subscriptions:
            self.untail()

    @coroutine
    def tail(self, query=None, fields=None, last_id=None):
        if self.tailing:
            raise RuntimeError('This storage is already tailing')
        self.tailing = True
        if query is None:
            query = {}
        last_object_id = None

        if last_id is None:
            cursor = (self.col.find()
                      .sort('$natural', pymongo.DESCENDING)
                      .limit(1))
            if (yield cursor.fetch_next):
                last_object_id = cursor.next_object()['_id']
        elif last_id != 0:
            last_object_id = ObjectId(last_id)

        if last_object_id:
            query['_id'] = {'$gt': ObjectId(last_id)}

        cursor = self.col.find(query, fields)

        while self.tailing:
            if (yield cursor.fetch_next):
                doc = cursor.next_object()
                self.signal_manager.send_catch_log(
                    self.signals['tailed'], data=doc
                )
                last_object_id = doc['_id']
            else:
                if last_object_id:
                    query['_id'] = {'$gt': last_object_id}

                cursor = self.col.find(query, fields)
                yield sleep(1)

    def untail(self):
        self.tailing = False
