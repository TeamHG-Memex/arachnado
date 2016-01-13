import logging

from arachnado.utils.misc import json_encode
# A little monkey patching to have custom types encoded right
from jsonrpclib import jsonrpc
jsonrpc.jdumps = json_encode
import tornadorpc
from tornadorpc.json import JSONRPCHandler
from tornado.concurrent import Future

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
