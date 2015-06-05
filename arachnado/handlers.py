# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import itertools
from tornado import web

from .spider import get_crawler
from .monitor import Monitor
from .api import ApiHandler

at_root = lambda *args: os.path.join(os.path.dirname(__file__), *args)


def get_application(crawler_process):
    handlers = [
        (r"/", Index),
        (r"/help", Help),
        (r"/settings", Settings),
        (r"/start", StartCrawler, {'crawler_process': crawler_process}),
        (r"/ws", Monitor, {'crawler_process': crawler_process}),
    ]
    return web.Application(
        handlers=handlers,
        template_path=at_root("templates"),
        compiled_template_cache=False,
        static_path=at_root("static"),
        # no_keep_alive=True,
    )


class Index(web.RequestHandler):
    def get(self):
        return self.render("index.html")


class Help(web.RequestHandler):
    def get(self):
        return self.render("help.html")


class Settings(web.RequestHandler):
    def get(self):
        return self.render("settings.html")


class StartCrawler(ApiHandler, web.RequestHandler):
    """
    This endpoint starts crawling for a domain.
    """
    crawl_ids = itertools.count(1)

    def initialize(self, crawler_process):
        self.crawler_process = crawler_process

    def crawl(self, domain):
        crawler = get_crawler()
        crawl_id = next(self.crawl_ids)
        self.crawler_process.crawl(crawler, domain=domain, crawl_id=crawl_id)

    def post(self):
        if self.is_json:
            domain = self.json_args['domain']
            self.crawl(domain)
            return {"status": "ok"}
        else:
            domain = self.get_body_argument('domain')
            self.crawl(domain)
            self.redirect("/")
