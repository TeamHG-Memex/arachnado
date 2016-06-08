# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import logging

from tornado import websocket

from arachnado.utils.misc import json_encode


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
        # if event != "process:stats":
        #     print("-----------------================")
        #     print("write_event {} {}".format(event, data))
        message = None
        try:
            message = json_encode({'event': event, 'data': data})
        except Exception as e:
            logger.warn("Invalid event message skipped {} {} {}".format(e, event, data))
            return

        if message:
            try:
                self.write_message(message)
            except Exception as e:
                logger.warn("Error while sending message {}".format(e))

    def on_message(self, message):
        # print("-----------------================")
        # print("on message {}".format(message))
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
