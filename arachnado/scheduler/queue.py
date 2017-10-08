import logging
import random as rnd

from pymongo import ASCENDING
from scrapy.utils.reqser import request_to_dict, request_from_dict

from arachnado.utils.mongo import motor_from_uri
from . import picklecompat

logger = logging.getLogger(__name__)


class Base(object):
    """Per-spider queue/stack base class"""

    def __init__(self, server, spider, key, serializer=None, stats=None):
        """Initialize per-spider redis queue.

        Parameters:
            server -- redis connection
            spider -- spider instance
            key -- key for this queue (e.g. "%(spider)s:queue")

        """
        if serializer is None:
            # Backward compatibility.
            # TODO: deprecate pickle.
            serializer = picklecompat
        if not hasattr(serializer, 'loads'):
            raise TypeError("serializer does not implement 'loads' function: %r"
                            % serializer)
        if not hasattr(serializer, 'dumps'):
            raise TypeError("serializer '%s' does not implement 'dumps' function: %r"
                            % serializer)
        self.server = server
        self.spider = spider
        self.stats = stats
        self.key = key % {'spider': spider.name}
        self.serializer = serializer
        # self.queue_uri = self.spider.settings.get('MONGO_REQUESTS_QUEUE_URI')
        queue_uri_template = self.spider.settings.get('MONGO_QUEUE_URI_TEMPLATE', "{}/arachnado/queue")
        self.queue_uri = queue_uri_template.format(self.spider.settings.get('MOTOR_PIPELINE_URI'))
        self.queue_client, _, _, _, self.queue_col = \
            motor_from_uri(self.queue_uri)
        # self.queue_client = MongoClient(self.queue_uri)
        # self.queue_col = self.queue_client["arachnado"]["queue"]
#        self.queue_col.ensure_index('score', unique=False)
        self.redis_size_limit = self.spider.settings.get('MAX_REDIS_QUEUE_SIZE', 1000)
        self.redis_size_trigger_mult = self.spider.settings.get('MAX_REDIS_QUEUE_SIZE_TRIGGER', 0.8)

    def _encode_request(self, request):
        """Encode a request object"""
        obj = request_to_dict(request, self.spider)
        return self.serializer.dumps(obj)

    def _decode_request(self, encoded_request):
        """Decode an request previously encoded"""
        obj = self.serializer.loads(encoded_request)
        return request_from_dict(obj, self.spider)

    def __len__(self):
        """Return the length of the queue"""
        raise NotImplementedError

    def push(self, request):
        """Push a request"""
        raise NotImplementedError

    def pop(self, timeout=0):
        """Pop a request"""
        raise NotImplementedError

    def clear(self):
        """Clear queue/stack"""
        self.server.delete(self.key)


class SpiderPriorityQueue(Base):
    """Per-spider priority queue abstraction using redis sorted set and mongo collection"""

    def __len__(self):
        mongo_cnt = self._mongo_len()
        return self._redis_len() + mongo_cnt

    def _redis_len(self):
        return self.server.zcard(self.key)

    def _mongo_len(self):
        return 0

    def push(self, request):
        """Push a request"""
        if self._redis_len() >= self.redis_size_limit:
            redis_last_request = self._redis_pop(pos=-1)
            if redis_last_request:
                # check priority
                if redis_last_request.priority > request.priority:
                    self._redis_push(redis_last_request)
                    # TODO: check this
                    if not self._mongo_push(request):
                        self._redis_push(request)
                else:
                    # TODO: check this
                    if not self._mongo_push(redis_last_request):
                        self._redis_push(redis_last_request)
                    self._redis_push(request)
                if self.stats:
                    self.stats.inc_value('scheduler/composite/mongo', spider=self.spider)
        else:
            self._redis_push(request)
            if self.stats:
                self.stats.inc_value('scheduler/composite/redis', spider=self.spider)
        redis_queue_size = self._redis_len()
        if self.stats:
            self.stats.max_value('scheduler/composite/redis/max_queue', redis_queue_size, spider=self.spider)
            self.stats.set_value('scheduler/composite/redis/current_queue', redis_queue_size, spider=self.spider)

    def _redis_push(self, request):
        data = self._encode_request(request)
        score = -request.priority
        self.server.execute_command('ZADD', self.key, score, data)

    def _mongo_push(self, request):
        def cb_insert_result(res, error):
            logger.debug(res)
            if error:
                logger.error(error)

        queue_item = {
            "score": -request.priority,
            "data": self._encode_request(request),
            "random_score": rnd.random(),
            "spider": self.get_spider_name()
        }
        try:
            self.queue_col.insert(queue_item, callback=cb_insert_result)
        except Exception as ex:
            self.stats.inc_value('scheduler/composite/mongo/push/errors', spider=self.spider)
            logger.exception("Error while connecting to MONGO at {}".format(self.queue_uri))
        return True

    def get_spider_name(self):
        if self.spider:
            spider_name = self.spider.name
        else:
            spider_name = "unknown"
        return spider_name

    def _redis_pop(self, pos=0):
        pipe = self.server.pipeline()
        pipe.multi()
        pipe.zrange(self.key, pos, pos).zremrangebyrank(self.key, pos, pos)
        results, count = pipe.execute()
        if results:
            return self._decode_request(results[0])
        else:
            return None

    def pop(self, timeout=0):

        def cb_removed(res, error):
            logger.debug(res)
            if error:
                self.stats.inc_value('scheduler/composite/mongo/remove/errors', spider=self.spider)
                logger.error(error)
            else:
                self.stats.inc_value('scheduler/composite/mongo/removed', spider=self.spider)

        def cb_process_requests(reqs, error):
            if error:
                logger.error(error)
            else:
                logger.debug(len(reqs))
                for res in reqs:
                    self.queue_col.remove({"_id": res["_id"]}, callback=cb_removed)
                    request = self._decode_request(res["data"])
                    self._redis_push(request)
                    if self.stats:
                        self.stats.inc_value('scheduler/composite/redis', spider=self.spider)

        reqs_in_redis = self._redis_len()
        if (reqs_in_redis < self.redis_size_limit * self.redis_size_trigger_mult):
            try:
                self.queue_col.find({"spider": self.get_spider_name()})\
                    .sort([("score", ASCENDING), ("random_score", ASCENDING),])\
                    .limit(self.redis_size_limit - reqs_in_redis)\
                    .to_list(length=None, callback=cb_process_requests)
            except Exception as ex:
                self.stats.inc_value('scheduler/composite/mongo/pop/errors', spider=self.spider)
                logger.exception("Error while mongo pop from {}".format(self.queue_uri))
        return self._redis_pop()

    def clear(self):
        """Clear queue/stack"""
        self.server.delete(self.key)
        # yield self.queue_col.remove({"spider": self.get_spider_name()})


__all__ = ['SpiderPriorityQueue', ]
