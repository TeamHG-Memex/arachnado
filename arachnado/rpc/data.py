import logging
import json
import sys
from collections import deque
from tornado import gen
import tornado.ioloop
from bson.objectid import ObjectId
from bson.errors import InvalidId
from jsonrpc.dispatcher import Dispatcher

from arachnado.rpc.jobs import Jobs
from arachnado.rpc.sites import Sites
from arachnado.rpc.pages import Pages

from arachnado.crawler_process import agg_stats_changed, CrawlerProcessSignals as CPS
from arachnado.rpc.ws import RpcWebsocketHandler
from arachnado.utils.misc import json_encode

logger = logging.getLogger(__name__)


class DataRpcWebsocketHandler(RpcWebsocketHandler):
    """ basic class for Data API handlers"""
    stored_data = None
    delay_mode = False
    heartbeat_data = None
    i_args = None
    i_kwargs = None
    storages = None
    max_msg_size = 2**20

    def _send_event(self, data):
        return super(DataRpcWebsocketHandler, self).write_event(data, max_message_size=self.max_msg_size)

    def init_heartbeat(self, update_delay):
        if update_delay > 0 and not self.heartbeat_data:
            self.delay_mode = True
            self.heartbeat_data = tornado.ioloop.PeriodicCallback(
                lambda: self.send_updates(),
                update_delay
            )
            self.heartbeat_data.start()

    def cancel_subscription(self, subscription_id):
        storage = self.storages.pop(subscription_id, None)
        if storage:
            storage.on_close()
            return True
        else:
            return False

    def set_max_message_size(self, max_size):
        self.max_msg_size = max_size
        return True

    def initialize(self, *args, **kwargs):
        self.stored_data = deque()
        self.storages = {}
        self.i_args = args
        self.i_kwargs = kwargs
        self.cp = kwargs.get("crawler_process", None)
        self.dispatcher = Dispatcher()
        self.dispatcher["cancel_subscription"] = self.cancel_subscription
        self.dispatcher["set_max_message_size"] = self.set_max_message_size

    def on_close(self):
        logger.info("connection closed")
        for storage in self.storages.values():
            storage.on_close()
        if self.heartbeat_data:
            self.heartbeat_data.stop()
        super(DataRpcWebsocketHandler, self).on_close()

    def open(self):
        logger.info("new connection")
        super(DataRpcWebsocketHandler, self).open()

    def send_updates(self):
        while len(self.stored_data):
            item = self.stored_data.popleft()
            self._send_event(item)


class JobsDataRpcWebsocketHandler(DataRpcWebsocketHandler):
    mongo_id_mapping = None
    job_url_mapping = None
    stored_jobs_stats = None

    @gen.coroutine
    def subscribe_to_jobs(self, include=None, exclude=None, update_delay=0, last_job_id=None):
        self.init_heartbeat(update_delay)
        stor_id, storage = self.add_storage()
        jobs_storage = Jobs(self, *self.i_args, **self.i_kwargs)
        jobs_storage.callback_meta = stor_id
        jobs_storage.callback = self.on_jobs_tailed
        storage.add_jobs_subscription(jobs_storage, include=include, exclude=exclude, last_id=last_job_id)
        return {"datatype": "job_subscription_id",
                "id": stor_id}

    def add_storage(self):
        new_id = str(len(self.storages))
        storage = DataSubscription()
        self.storages[new_id] = storage
        return new_id, storage

    @gen.coroutine
    def write_event(self, data, aggregate=False):
        event_data = dict(data)
        if 'stats' in event_data:
            if not isinstance(event_data['stats'], dict):
                try:
                    event_data['stats'] = json.loads(event_data['stats'])
                except Exception as ex:
                    logger.warning("Invalid stats field in job {}".format(event_data.get("_id", "MISSING MONGO ID")))
        if aggregate and self.delay_mode:
            item_id = event_data.get("_id", None)
            if item_id:
                if item_id in self.stored_jobs_stats:
                    self.stored_jobs_stats[item_id]["stats"].update(event_data["stats"])
                else:
                    item = event_data
                    self.stored_jobs_stats[item_id] = item
            else:
                logger.warning("Job data without _id field from event {}".format(event))
        else:
            return self._send_event(event_data)

    def send_updates(self):
        super(JobsDataRpcWebsocketHandler, self).send_updates()
        for job_id in set(self.stored_jobs_stats.keys()):
            item = self.stored_jobs_stats.pop(job_id, None)
            if item:
                self._send_event(item)

    def initialize(self, *args, **kwargs):
        super(JobsDataRpcWebsocketHandler, self).initialize(*args, **kwargs)
        self.dispatcher["subscribe_to_jobs"] = self.subscribe_to_jobs
        self.mongo_id_mapping = {}
        self.job_url_mapping = {}
        self.stored_jobs_stats = {}

    def on_close(self):
        logger.debug("connection closed")
        if self.cp:
            self.cp.signals.disconnect(self.on_stats_changed, agg_stats_changed)
            self.cp.signals.disconnect(self.on_spider_closed, CPS.spider_closed)
        super(JobsDataRpcWebsocketHandler, self).on_close()

    def open(self):
        logger.debug("new connection")
        super(JobsDataRpcWebsocketHandler, self).open()
        if self.cp:
            self.cp.signals.connect(self.on_stats_changed, agg_stats_changed)
            self.cp.signals.connect(self.on_spider_closed, CPS.spider_closed)

    def on_stats_changed(self, changes, crawler):
        job_id = crawler.spider.crawl_id
        data = {"stats": changes}
        # same as crawl_id
        data["id"] = job_id
        # mongo id
        data["_id"] = self.mongo_id_mapping.get(job_id, "")
        # job url
        data["urls"] = self.job_url_mapping.get(job_id, "")
        allowed = False
        for storage in self.storages.values():
            allowed = allowed or job_id in storage.job_ids
        if allowed:
            self.write_event(data, aggregate=True)

    def on_spider_closed(self, spider):
        if self.cp:
            for job in self.cp.jobs:
                job_id = job["id"]
                allowed = False
                if job_id:
                    for storage in self.storages.values():
                        allowed = allowed or job_id in storage.job_ids
                if allowed:
                    self.write_event(job)

    def on_jobs_tailed(self, data, callback_meta=None):
        if "id" in data and callback_meta:
            self.storages[callback_meta].job_ids.add(data["id"])
            self.mongo_id_mapping[data["id"]] = data.get("_id", None)
            self.job_url_mapping[data["id"]] = data.get("urls", None)
        self.write_event(data)


class PagesDataRpcWebsocketHandler(DataRpcWebsocketHandler):
    """ pages API"""

    @gen.coroutine
    def subscribe_to_pages(self, urls=None, url_groups=None):
        result = {
            "datatype": "pages_subscription_id",
            "single_subscription_id": "",
            "id": {},
        }
        if urls:
            result["single_subscription_id"] = yield self.create_subscribtion_to_urls(urls)
        if url_groups:
            res = {}
            for group_id in url_groups:
                res[group_id] = yield self.create_subscribtion_to_urls(url_groups[group_id])
            result["id"] = res
        if not urls and not url_groups:
            stor_id, storage = self.add_storage()
            result["single_subscription_id"] = stor_id
            storage.pages.subscribe(query={})
        raise gen.Return(result)

    @gen.coroutine
    def create_subscribtion_to_urls(self, urls):
        jobs_to_subscribe = []
        stor_id, storage = self.add_storage()
        result = stor_id
        for url in urls:
            last_id = urls[url]
            jobs = Jobs(self, *self.i_args, **self.i_kwargs)
            jobs.callback_meta = {
                "subscription_id":stor_id,
                "last_id":last_id
            }
            jobs.callback = self.job_query_callback
            jobs_q = self.create_jobs_query(url)
            jobs_ds = yield jobs.storage.fetch(jobs_q)
            job_ids =[x["_id"] for x in jobs_ds]
            if job_ids:
                storage.job_ids.update(job_ids)
                pages_query = storage.create_pages_query(job_ids, last_id)
                storage.filters.append(pages_query)
                storage.jobs.append(jobs)
                jobs_to_subscribe.append([jobs_q,  jobs])
            else:
                logger.info("No jobs found for url {}".format(url))
        storage.subscribe_to_pages()
        for jobs_q, jobs in jobs_to_subscribe:
            jobs.subscribe(query=jobs_q)
        raise gen.Return(result)

    @gen.coroutine
    def write_event(self, data, aggregate=False):
        if aggregate and self.delay_mode:
            self.stored_data.append(data)
        else:
            return self._send_event(data)

    def initialize(self, *args, **kwargs):
        super(PagesDataRpcWebsocketHandler, self).initialize(*args, **kwargs)
        self.dispatcher["subscribe_to_pages"] = self.subscribe_to_pages

    @gen.coroutine
    def job_query_callback(self, data, callback_meta=None):
        if "_id" in data and callback_meta:
            storage = self.storages[callback_meta["subscription_id"]]
            job_id = data["_id"]
            storage.update_pages_subscription(job_id, callback_meta["last_id"])
        else:
            logger.warning("Jobs callback with incomplete data")

    def on_pages_tailed(self, data, callback_meta=None):
        self.write_event(data)

    def create_jobs_query(self, url):
        if url:
            return {"urls":{'$regex': url }}
        else:
            return {}

    def add_storage(self):
        new_id = str(len(self.storages))
        pages = Pages(self, *self.i_args, **self.i_kwargs)
        pages.callback = self.on_pages_tailed
        self.storages[new_id] = DataSubscription(pages)
        return new_id, self.storages[new_id]

    def cancel_subscription(self, subscription_id):
        storage = self.storages.pop(subscription_id, None)
        if storage:
            storage.on_close()
            return True
        else:
            return False


class DataSubscription(object):

    def __init__(self, pages_storage=None):
        self.pages = pages_storage
        self.jobs = []
        self.job_ids = set([])
        self.filters = []

    def on_close(self):
        for jobs in self.jobs:
            jobs._on_close()
        if self.pages:
            self.pages._on_close()

    def subscribe_to_pages(self, require_filters=True):
        if self.filters:
            if len(self.filters) == 1:
                self.pages.subscribe(query=self.filters[0])
            elif len(self.filters) > 1:
                self.pages.subscribe(query={"$or": self.filters})
        elif not require_filters:
            self.pages.subscribe(query={})
        else:
            logger.warning("No subscription - empty filter list")

    def add_jobs_subscription(self, jobs_storage, include=None, exclude=None, last_id=None):
        jobs_query = self.create_jobs_subscription_query(include=include, exclude=exclude, last_id=last_id)
        self.jobs.append(jobs_storage)
        jobs_storage.subscribe(query=jobs_query)

    def update_pages_subscription(self, job_id, last_id):
        if job_id not in self.job_ids:
            # stop pages subscription
            self.pages.unsubscribe()
            # create new pages query
            pages_query = self.create_pages_query([job_id], last_id)
            self.filters.append(pages_query)
            # subscribe to pages
            self.subscribe_to_pages()
        else:
            logger.debug("Already subscribed to job {}".format(job_id))

    def create_pages_query(self, job_ids=None, last_id=None):
        filters = []
        job_conditions_lst = []
        if job_ids:
            for job_id in job_ids:
                job_conditions_lst.append({"_job_id":{'$eq': str(job_id) }})
        if job_conditions_lst:
            if len(job_conditions_lst) > 1:
                filters.append({"$or": job_conditions_lst})
            else:
                filters.append(job_conditions_lst[0])
        if last_id:
            try:
                page_id = ObjectId(last_id)
                filters.append({"_id":{"$gt":page_id}})
            except InvalidId:
                logger.warning("Invalid ObjectID: {}, will use job ids filter only.".format(last_id))
        items_q = {}
        if len(filters) == 1:
            items_q = filters[0]
        elif len(filters) > 1:
            items_q = {"$and": filters}
        return items_q

    def create_jobs_subscription_query(self, include, exclude, last_id):
        conditions = []
        if last_id:
            conditions.append({"_id":{"$gt":last_id}})
        if include:
            for inc_str in include:
                conditions.append({"urls":{'$regex': inc_str }})
        if exclude:
            for exc_str in exclude:
                conditions.append({"urls":{'$regex': '^((?!' + exc_str + ').)*$'}})
        jobs_q = {}
        if len(conditions) == 1:
            jobs_q = conditions[0]
        elif len(conditions):
            jobs_q = {"$and": conditions }
        return jobs_q