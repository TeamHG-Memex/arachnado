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
        # Parse FancyWebSocket message format: {event: "rpc:request", data: {...}}
        try:
            msg_obj = json.loads(message)
            if isinstance(msg_obj, dict) and 'event' in msg_obj and 'data' in msg_obj:
                if msg_obj['event'] == 'rpc:request':
                    # Extract the JSON-RPC request from the data field
                    rpc_request = json.dumps(msg_obj['data'])
                    self.handle_request(rpc_request)
                else:
                    logger.warning("Unexpected event type: %s", msg_obj['event'])
            else:
                # Fallback to direct handling for backward compatibility
                self.handle_request(message)
        except (ValueError, KeyError, TypeError) as e:
            logger.error("Failed to parse WebSocket message: %s", e)
            # Try direct handling as fallback
            self.handle_request(message)

    def send_data(self, data):
        # Wrap JSON-RPC response in FancyWebSocket format
        if isinstance(data, six.string_types):
            data = json.loads(data)
        wrapped_response = {
            'event': 'rpc:response',
            'data': data
        }
        self.write_event(wrapped_response)

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
