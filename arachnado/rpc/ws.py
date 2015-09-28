import json
import logging

import jsonrpclib
from jsonrpclib.jsonrpc import Fault
from tornadorpc.json import JSONRPCHandler, JSONRPCParser
from tornado import websocket
from tornado.concurrent import Future

from arachnado.utils.misc import json_encode


logger = logging.getLogger(__name__)
jsonrpclib.config.use_jsonclass = False


class JsonRpcWebsocketHandler(websocket.WebSocketHandler):

    def on_message(self, message):
        self._results = []
        try:
            msg = json.loads(message.encode('utf-8'))
            event, data = msg['event'], msg['data']
        except (TypeError, ValueError):
            logger.warn("Invalid message skipped" + message[:500])
            return
        if event == 'rpc:request':
            self.on_event(data)
        else:
            logger.warn("Unsupported event type: " + event)

    def on_event(self, data):
        self._RPC_.run(self, json_encode(data))

    def result(self, result):
        if isinstance(result, Future):
            result.add_done_callback(self._result)
        else:
            self._result(result)

    def _result(self, result):
        if isinstance(result, Future):
            result = result.result()
        self._results.append(result)
        self._RPC_finished = False
        self._RPC_.response(self)

    def on_result(self, data):
        return self.write_event('rpc:response', data)

    def write_event(self, event, data):
        message = json_encode({'event': event, 'data': json.loads(data)})
        self.write_message(message)
