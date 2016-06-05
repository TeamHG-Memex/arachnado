# -*- coding: utf-8 -*-
import tornado
import json
from arachnado.rpc.data import DataRpcWebsocketHandler
from arachnado.storages.mongotail import MongoTailStorage


def get_app(ws_uri):
    items_uri = "mongodb://localhost:27017/arachnado/items"
    jobs_uri = "mongodb://localhost:27017/arachnado/jobs"
    job_storage = MongoTailStorage(jobs_uri, cache=True)
    item_storage = MongoTailStorage(items_uri)
    context = {
        'crawler_process': None,
        'job_storage': job_storage,
        'item_storage': item_storage,
    }
    app = tornado.web.Application([
        (ws_uri, DataRpcWebsocketHandler, context)
    ])
    return app

