import logging

from arachnado.utils.misc import json_encode
# A little monkey patching to have custom types encoded right
# from jsonrpclib import jsonrpc
# jsonrpc.jdumps = json_encode
# import tornadorpc
import json
from tornado import gen
import tornado.ioloop
from bson.objectid import ObjectId
from jsonrpc.dispatcher import Dispatcher

from arachnado.rpc.jobs import Jobs
from arachnado.rpc.sites import Sites
from arachnado.rpc.pages import Pages

from arachnado.crawler_process import agg_stats_changed, CrawlerProcessSignals as CPS
from arachnado.rpc.ws import RpcWebsocketHandler

logger = logging.getLogger(__name__)
# tornadorpc.config.verbose = True
# tornadorpc.config.short_errors = True


class DataRpcWebsocketHandler(RpcWebsocketHandler):
    """ jobs and pages API"""
    stored_data = []
    delay_mode = False
    event_types = ['stats:changed', 'pages.tailed']
    data_hb = None
    i_args = None
    i_kwargs = None
    storages = {}
    # TODO: allow client to update this
    max_msg_size = 2**20

    def subscribe_to_pages(self, site_ids={}, update_delay=0):
        mongo_q = self.create_pages_query(site_ids=site_ids)
        self.init_hb(update_delay)
        return self.add_storage(mongo_q, storage=self.create_pages_storage_link())

    def subscribe_to_jobs(self, include=[], exclude=[], update_delay=0):
        mongo_q = self.create_jobs_query(include=include, exclude=exclude)
        self.init_hb(update_delay)
        return self.add_storage(mongo_q, storage=self.create_jobs_storage_link())

    @gen.coroutine
    def write_event(self, event, data, handler_id=None):
        if event == 'jobs.tailed' and "id" in data and handler_id:
            self.storages[handler_id]["job_ids"].add(data["id"])
        if event in ['stats:changed', 'jobs:state']:
            if event == 'stats:changed':
                job_id = data[0]
            else:
                job_id = data["id"]
            allowed = False
            for storage in self.storages.values():
                allowed = allowed or job_id in storage["job_ids"]
            if not allowed:
                return
        if event in self.event_types and self.delay_mode:
            self.stored_data.append({"event":event, "data":data})
        else:
            return self._send_event(event, data)

    def _send_event(self, event, data):
        message = json_encode({'event': event, 'data': data})
        if len(message) < self.max_msg_size:
            # logging.info("{}: {}: {}".format(self.cnt, event, len(message)))
            # self.cnt += 1
            return super(DataRpcWebsocketHandler, self).write_event(event, data)

    def init_hb(self, update_delay):
        if update_delay > 0 and not self.data_hb:
            self.delay_mode = True
            self.data_hb = tornado.ioloop.PeriodicCallback(
                lambda: self.send_updates(),
                update_delay
            )
            self.data_hb.start()

    def add_storage(self, mongo_q, storage):
        self.dispatcher.add_object(storage)
        new_id = str(len(self.storages))
        self.storages[new_id] = {
            "storage": storage,
            "job_ids": set([])
        }
        storage.handler_id = new_id
        storage.subscribe(query=mongo_q)
        return new_id

    def create_jobs_query(self, include, exclude):
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
        storage = self.storages.pop(subscription_id, None)
        if storage:
            storage._on_close()
            return True
        else:
            return False

    def initialize(self, *args, **kwargs):
        self.i_args = args
        self.i_kwargs = kwargs
        self.cp = kwargs.get("crawler_process", None)
        self.dispatcher = Dispatcher()
        self.dispatcher["subscribe_to_pages"] = self.subscribe_to_pages
        self.dispatcher["subscribe_to_jobs"] = self.subscribe_to_jobs
        self.dispatcher["cancel_subscription"] = self.cancel_subscription

    def create_jobs_storage_link(self):
        jobs = Jobs(self, *self.i_args, **self.i_kwargs)
        return jobs

    def on_close(self):
        # import traceback
        # traceback.print_stack()
        logger.info("connection closed")
        if self.cp:
            self.cp.signals.disconnect(self.on_stats_changed, agg_stats_changed)
            self.cp.signals.disconnect(self.on_spider_closed, CPS.spider_closed)
        for storage in self.storages.values():
            storage["storage"]._on_close()
        if self.data_hb:
            self.data_hb.stop()
        super(DataRpcWebsocketHandler, self).on_close()

    def open(self):
        logger.info("new connection")
        super(DataRpcWebsocketHandler, self).open()
        if self.cp:
            self.cp.signals.connect(self.on_stats_changed, agg_stats_changed)
            self.cp.signals.connect(self.on_spider_closed, CPS.spider_closed)

    def on_spider_closed(self, spider):
        if self.cp:
            for job in self.cp.jobs:
                self.write_event("jobs:state", job)

    def on_stats_changed(self, changes, crawler):
        crawl_id = crawler.spider.crawl_id
        self.write_event("stats:changed", [crawl_id, changes])

    def send_updates(self):
        print("send_updates: {}".format(len(self.stored_data)))
        while len(self.stored_data):
            item = self.stored_data.pop()
            return self._send_event(item["event"], item["data"])

    def create_pages_storage_link(self):
        pages = Pages(self, *self.i_args, **self.i_kwargs)
        return pages

    def create_pages_query(self, site_ids):
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

