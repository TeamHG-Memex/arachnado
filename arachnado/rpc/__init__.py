import logging

from tornadorpc.json import JSONRPCHandler

from arachnado.rpc.sites import SitesRpc
from arachnado.rpc.ws import JsonRpcWebsocketHandler


logger = logging.getLogger(__name__)


class MainRpcHttpHandler(JSONRPCHandler):

    def initialize(self, *args, **kwargs):
        self.sites = SitesRpc(*args, **kwargs)


class MainRpcWebsocketHandler(JsonRpcWebsocketHandler, MainRpcHttpHandler):
    pass
