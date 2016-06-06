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
        try:
            msg = json.loads(message)
            event, data = msg['event'], msg['data']
        except (TypeError, ValueError):
            logger.warn('Invalid message skipped: {!r}'.format(message[:500]))
            return
        if event == 'rpc:request':
            self.handle_request(json.dumps(data))
        else:
            logger.warn('Unsupported event type: {!r}'.format(event))

    def send_data(self, data):
        self.write_event('rpc:response', data)

    @gen.coroutine
    def write_event(self, event, data):
        if isinstance(data, six.string_types):
            data = json.loads(data)
        message = json_encode({'event': event, 'data': data})
        try:
            self.write_message(message)
        except websocket.WebSocketClosedError:
            pass

    def open(self):
        """ Forward open event to resource objects.
        """
        for resource in self._resources():
            if hasattr(resource, '_on_open'):
                resource._on_open()
        self._pinger = PeriodicCallback(lambda: self.ping(b'PING'), 1000 * 15)
        self._pinger.start()

    def on_close(self):
        """ Forward on_close event to resource objects.
        """
        for resource in self._resources():
            if hasattr(resource, '_on_close'):
                resource._on_close()
        self._pinger.stop()

    def _resources(self):
        for resource_name, resource in self.__dict__.items():
            if hasattr(RequestHandler, resource_name):
                continue
            yield resource

