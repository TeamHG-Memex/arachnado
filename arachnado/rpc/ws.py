import sys
import json
import logging
import six

from tornado.ioloop import PeriodicCallback
from tornado.concurrent import Future
from tornado.web import RequestHandler
from tornado import websocket, gen

from arachnado.utils.misc import json_encode
from arachnado.rpc import ArachnadoRPC


logger = logging.getLogger(__name__)


class RpcWebsocketHandler(ArachnadoRPC, websocket.WebSocketHandler):
    """ JsonRpc router for WS stream.
    """

    def on_message(self, message):
        self.handle_request(message)

    def send_data(self, data):
        self.write_event(data)

    @gen.coroutine
    def write_event(self, data, max_message_size=0):
        if isinstance(data, six.string_types):
            message = data
        else:
            message = json_encode(data)
        try:
            if sys.getsizeof(message) < max_message_size or not max_message_size:
                self.write_message(message)
            else:
                logger.info("Message size exceeded. Message wasn't sent.")
        except websocket.WebSocketClosedError:
            pass

    def open(self):
        """ Forward open event to resource objects.
        """
        logger.debug("Connection opened %s", self)
        for resource in self.rpc_objects:
            if hasattr(resource, '_on_open'):
                resource._on_open()
        self._pinger = PeriodicCallback(lambda: self.ping(b'PING'), 1000 * 15)
        self._pinger.start()
        logger.debug("Pinger initiated %s", self)

    def on_close(self):
        """ Forward on_close event to resource objects.
        """
        logger.debug("Connection closed %s", self)
        for resource in self.rpc_objects:
            if hasattr(resource, '_on_close'):
                resource._on_close()
        self._pinger.stop()
