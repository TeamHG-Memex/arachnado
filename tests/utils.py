# -*- coding: utf-8 -*-
import os
import tornado
import json
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from arachnado.rpc.data import PagesDataRpcWebsocketHandler, JobsDataRpcWebsocketHandler
from arachnado.storages.mongotail import MongoTailStorage
from arachnado.utils.mongo import motor_from_uri


def get_mongo_db():
    client = MongoClient('mongodb://localhost:27017/')
    return client["arachnado-test"]


def get_db_uri():
    return "mongodb://localhost:27017/arachnado-test"


def get_app(ws_pages_uri, ws_jobs_uri):
    db_uri = get_db_uri()
    items_uri = "{}/items".format(db_uri)
    jobs_uri = "{}/jobs".format(db_uri)
    job_storage = MongoTailStorage(jobs_uri, cache=True)
    item_storage = MongoTailStorage(items_uri)
    context = {
        'crawler_process': None,
        'job_storage': job_storage,
        'item_storage': item_storage,
    }
    app = tornado.web.Application([
        (ws_pages_uri, PagesDataRpcWebsocketHandler, context),
        (ws_jobs_uri, JobsDataRpcWebsocketHandler, context),
    ])
    return app


def init_db():
    db = get_mongo_db()
    collections = ["jobs", "items"]
    for collection in collections:
        col_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "{}.jl".format(collection))
        col = db[collection]
        with open(col_path, "r") as fin:
            for text_line in fin:
                record = json.loads(text_line)
                try:
                    col.insert(record)
                except DuplicateKeyError:
                    pass


def clear_db():
    db = get_mongo_db()
    collections = ["jobs", "items"]
    for collection in collections:
        col = db[collection]
        col.drop()