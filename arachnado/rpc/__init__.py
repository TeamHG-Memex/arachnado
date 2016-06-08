from functools import partial

from jsonrpc import JSONRPCResponseManager
from jsonrpc.dispatcher import Dispatcher
from tornado.web import RequestHandler, asynchronous
from tornado.concurrent import Future

from arachnado.utils.misc import json_encode
from arachnado.rpc.jobs import Jobs
from arachnado.rpc.sites import Sites
from arachnado.rpc.pages import Pages


class ArachnadoRPC(object):
    """ Base class for all Arachnado RPC resources.
    """
    def initialize(self, *args, **kwargs):
        self.dispatcher = Dispatcher()
        self.dispatcher.add_object(Jobs(self, *args, **kwargs))
        self.dispatcher.add_object(Sites(self, *args, **kwargs))
        self.dispatcher.add_object(Pages(self, *args, **kwargs))

    def handle_request(self, body):
        response = JSONRPCResponseManager.handle(body, self.dispatcher)
        if isinstance(response.result, Future):
            response.result.add_done_callback(
                partial(self.on_done, data=response.data))
        else:
            self.send_data(response.data)

    def on_done(self, future, data):
        data['result'] = future.result()
        self.send_data(data)

    def send_data(self, data):
        raise NotImplementedError


class RpcHttpHandler(ArachnadoRPC, RequestHandler):
    """ JsonRpc router for REST requests.
    """
    @asynchronous
    def post(self):
        self.handle_request(self.request.body)

    def send_data(self, data):
        self.write(json_encode(data))
        self.finish()
