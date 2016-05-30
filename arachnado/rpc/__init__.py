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
        print("MainRpcHttpHandler init")
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
    job_info = {}
    delay_mode = False
    job_event_type = 'jobs.tailed'
    job_hb = None

    @gen.coroutine
    def write_event(self, event, data):
        print("write_event!!!!!!!!!!!!!")
        if event == self.job_event_type and self.delay_mode:
            self.job_info[data["id"]] = data
        else:
            return super(MainRpcWebsocketHandler, self).write_event(event, data)

    def subscribe_to_jobs(self, include=[], exclude=[], update_delay=0):
        print("subscribe_to_jobs!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(include)
        print(exclude)
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
        if update_delay > 0:
            self.delay_mode = True
            self.job_hb = tornado.ioloop.PeriodicCallback(
                lambda: self.send_updates(),
                update_delay
            )
            self.job_hb.start()
        self.jobs.subscribe(query=jobs_q)

    def initialize(self, *args, **kwargs):
        print("JobsRpcWebsocketHandler init")
        self.jobs = JobsRpc(self, *args, **kwargs)

    def send_updates(self):
        for job_id in self.job_info:
            res = super(JobsRpcWebsocketHandler, self).write_event(self.job_event_type, self.job_info[job_id])
            self.job_info.pop(job_id)
            return res


class ItemsRpcWebsocketHandler(MainRpcWebsocketHandler):
    """ items info for WS stream"""
    items = []
    delay_mode = False
    page_event_type = 'pages.tailed'
    item_hb = None

    @gen.coroutine
    def write_event(self, event, data):
        print("write_event!!!!!!!!!!!!!")
        if event == self.page_event_type and self.delay_mode:
            self.items.append(data)
        else:
            return super(MainRpcWebsocketHandler, self).write_event(event, data)

    def subscribe_to_items(self, site_ids={}, update_delay=0):
        print("subscribe_to_items!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(site_ids)
        # print(exclude)
        conditions = []
        for site in site_ids:
            conditions.append(
                {"$and":[{"url":{"$regex": site + '.*'}},
                    {"_id":{"$gt":site_ids[site]}}
                ]}
            )
        items_q = {}
        if len(conditions) == 1:
            items_q = conditions[0]
        elif len(conditions):
            items_q = {"$or": conditions }
        if update_delay > 0:
            self.delay_mode = True
            self.item_hb = tornado.ioloop.PeriodicCallback(
                lambda: self.send_updates(),
                update_delay
            )
            self.item_hb.start()
        self.pages.subscribe(query=items_q)

    def initialize(self, *args, **kwargs):
        print("ItemsRpcWebsocketHandler init")
        self.pages = PagesRpc(self, *args, **kwargs)

    def send_updates(self):
        for item in self.items:
            self.items.remove(item)
            return super(ItemsRpcWebsocketHandler, self).write_event(self.page_event_type, item)

