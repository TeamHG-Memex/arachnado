# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import logging

from tornado import websocket

from arachnado.utils import json_encode


logger = logging.getLogger(__name__)


class BaseWSHandler(websocket.WebSocketHandler):
    """
    A base class which knows how to communicate with a client.
    All messages are JSON-encoded objects ``{"event": name, "data": data}``.

    Subclasses should use ``on_event`` instead of ``on_message`` and
    ``write_event`` instead of ``write_message``.
    """

    def write_event(self, event, data):
        """ Send a message to the client """
        message = json_encode({'event': event, 'data': data})
        self.write_message(message)

    def on_message(self, message):
        try:
            msg = json.loads(message)
            event, data = msg['event'], msg['data']
        except Exception as e:
            logger.warn("Invalid message skipped" + message[:500])
            return
        self.on_event(event, data)

    def on_event(self, event, data):
        """ This method is called when a message is received from a client """
        pass

    def on_open(self, *args, **kwargs):
        """ ``open`` alias, for consistency """

    def open(self, *args, **kwargs):
        self.on_open(*args, **kwargs)
