# -*- coding: utf-8 -*-
import os
import tornado
import json
from arachnado.rpc.data import PagesDataRpcWebsocketHandler, JobsDataRpcWebsocketHandler
from arachnado.storages.mongotail import MongoTailStorage
from arachnado.utils.mongo import motor_from_uri


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


@tornado.gen.coroutine
def import_file(file_path, mongo_uri):
    _, _, _, _, col = motor_from_uri(mongo_uri)
    # col.drop()
    with open(file_path, "r") as fin:
        for text_line in fin:
            record = json.loads(text_line)
            yield col.insert(record)


@tornado.gen.coroutine
def init_db():
    db_uri = get_db_uri()
    jobs_uri = "{}/jobs".format(db_uri)
    jobs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "jobs.jl")
    import_file(jobs_path, jobs_uri)
    items_uri = "{}/items".format(db_uri)
    items_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "items.jl")
    import_file(items_path, items_uri)