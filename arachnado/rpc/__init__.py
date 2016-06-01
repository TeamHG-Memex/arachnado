import logging

from arachnado.utils.misc import json_encode
# A little monkey patching to have custom types encoded right
from jsonrpclib import jsonrpc
jsonrpc.jdumps = json_encode
import tornadorpc
from tornadorpc.json import JSONRPCHandler
from tornado.concurrent import Future
from tornado import gen
import tornado.ioloop
from bson.objectid import ObjectId

from arachnado.rpc.jobs import JobsRpc
from arachnado.rpc.sites import SitesRpc
from arachnado.rpc.pages import PagesRpc
from arachnado.rpc.ws import JsonRpcWebsocketHandler


logger = logging.getLogger(__name__)
tornadorpc.config.verbose = True
tornadorpc.config.short_errors = True


class MainRpcHttpHandler(JSONRPCHandler):
    """ Main JsonRpc router for REST requests"""

    def initialize(self, *args, **kwargs):
        # print("MainRpcHttpHandler init")
        self.jobs = JobsRpc(self, *args, **kwargs)
        self.sites = SitesRpc(self, *args, **kwargs)
        self.pages = PagesRpc(self, *args, **kwargs)

    def result(self, result):
        if isinstance(result, Future):
            result.add_done_callback(self._result)
        else:
            self._result(result)

    def _result(self, result):
        if isinstance(result, Future):
            result = result.result()
        self._results.append(result)
        self._RPC_.response(self)


class MainRpcWebsocketHandler(JsonRpcWebsocketHandler, MainRpcHttpHandler):
    """ Main JsonRpc router for WS stream"""


class JobsRpcWebsocketHandler(MainRpcWebsocketHandler):
    """ jobs info for WS stream"""
    stored_data = []
    delay_mode = False
    event_types = ['jobs.tailed']
    data_hb = None
    i_args = None
    i_kwargs = None
    storages = {}

    @gen.coroutine
    def write_event(self, event, data):
        # print("write_event!!!!!!!!!!!!!")
        if event in self.event_types and self.delay_mode:
            self.stored_data.append({"event":event, "data":data})
        else:
            return super(MainRpcWebsocketHandler, self).write_event(event, data)

    def init_hb(self, update_delay):
        if update_delay > 0:
            self.delay_mode = True
            self.data_hb = tornado.ioloop.PeriodicCallback(
                lambda: self.send_updates(),
                update_delay
            )
            self.data_hb.start()

    def add_storage(self, mongo_q):
        storage = self.create_storage_link()
        storage.subscribe(query=mongo_q)
        new_id = str(len(self.storages))
        self.storages[new_id] = storage
        return new_id

    def subscribe_to_jobs(self, include=[], exclude=[], update_delay=0):
        mongo_q = self.create_query(include=include, exclude=exclude)
        self.init_hb(update_delay)
        return self.add_storage(mongo_q)

    def create_query(self, **kwargs):
        include = kwargs.get("include", [])
        exclude = kwargs.get("exclude", [])
        conditions = []
        for inc_str in include:
            conditions.append({"urls":{'$regex': '.*' + inc_str + '.*'}})
        for exc_str in exclude:
            conditions.append({"urls":{'$regex': '^((?!' + exc_str + ').)*$'}})
        jobs_q = {}
        if len(conditions) == 1:
            jobs_q = conditions[0]
        elif len(conditions):
            jobs_q = {"$and": conditions }
        return jobs_q

    def cancel_subscription(self, subscription_id):
        storage = self.storages.pop(subscription_id)
        storage._on_close()

    def initialize(self, *args, **kwargs):
        self.i_args = args
        self.i_kwargs = kwargs
        # # print("JobsRpcWebsocketHandler init")
        # pass

    def create_storage_link(self):
        return JobsRpc(self, *self.i_args, **self.i_kwargs)

    def send_updates(self):
        print("send_updates: {}".format(len(self.stored_data)))
        while len(self.stored_data):
            item = self.stored_data.pop()
            super(MainRpcWebsocketHandler, self).write_event(item["event"], item["data"])


class ItemsRpcWebsocketHandler(JobsRpcWebsocketHandler):
    """ items info for WS stream"""
    #TODO: create basic abstract class
    event_types = ['pages.tailed']

    def create_storage_link(self):
        return PagesRpc(self, *self.i_args, **self.i_kwargs)

    def create_query(self, **kwargs):
        site_ids = kwargs.get("site_ids", {})
        conditions = []
        for site in site_ids:
            if "url_field" in site_ids[site]:
                url_field_name = site_ids[site]["url_field"]
                item_id = site_ids[site]["id"]
            else:
                url_field_name = "url"
                item_id = site_ids[site]
            item_id = ObjectId(item_id)
            conditions.append(
                {"$and":[{url_field_name:{"$regex": site + '.*'}},
                    {"_id":{"$gt":item_id}}
                ]}
            )
        items_q = {}
        if len(conditions) == 1:
            items_q = conditions[0]
        elif len(conditions):
            items_q = {"$or": conditions}
        return items_q

    def subscribe_to_items(self, site_ids={}, update_delay=0):
        mongo_q = self.create_query(site_ids=site_ids)
        self.init_hb(update_delay)
        return self.add_storage(mongo_q)   