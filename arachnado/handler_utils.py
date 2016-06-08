# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
from tornado import web


class ApiHandler(web.RequestHandler):
    """ Base handler for JSON APIs """

    def prepare(self):
        if self.request.headers.get("Content-Type", "").startswith("application/json"):
            self.json_args = json.loads(self.request.body.decode("utf-8"))
            self.is_json = True
        else:
            self.json_args = None
            self.is_json = False


class NoEtagsMixin(object):
    """ A mixin to fix browser caching of static files referred from a page """
    def compute_etag(self):
        return None
