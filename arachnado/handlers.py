# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

from tornado.web import Application, RequestHandler, url

from arachnado.utils import json_encode
from arachnado.spider import create_crawler
from arachnado.monitor import Monitor
from arachnado.handler_utils import ApiHandler, NoEtagsMixin

at_root = lambda *args: os.path.join(os.path.dirname(__file__), *args)


def get_application(crawler_process):
    handlers = [
        url(r"/", Index, {'crawler_process': crawler_process}, name="index"),
        url(r"/help", Help, name="help"),
        url(r"/settings", Settings, name="settings"),
        url(r"/start", StartCrawler, {'crawler_process': crawler_process}, name="start"),
        url(r"/ws-updates", Monitor, {'crawler_process': crawler_process}, name="ws"),
    ]
    return Application(
        handlers=handlers,
        template_path=at_root("templates"),
        compiled_template_cache=False,
        static_path=at_root("static"),
        # no_keep_alive=True,
        compress_response=True,
    )


class Index(NoEtagsMixin, RequestHandler):
    def initialize(self, crawler_process):
        self.crawler_process = crawler_process

    def get(self):
        jobs = self.crawler_process.jobs
        proc_stats = self.crawler_process.procmon.get_recent()
        initial_data_json = json_encode({
            "jobs": jobs,
            "processStats": proc_stats,
        })
        return self.render("index.html", initial_data_json=initial_data_json)


class Help(RequestHandler):
    def get(self):
        return self.render("help.html")


class Settings(RequestHandler):
    def get(self):
        return self.render("settings.html")


class StartCrawler(ApiHandler, RequestHandler):
    """
    This endpoint starts crawling for a domain.
    """
    def initialize(self, crawler_process):
        self.crawler_process = crawler_process

    def crawl(self, domain):
        crawler = create_crawler()
        self.crawler_process.crawl(crawler, domain=domain)

    def post(self):
        if self.is_json:
            domain = self.json_args['domain']
            self.crawl(domain)
            return {"status": "ok"}
        else:
            domain = self.get_body_argument('domain')
            self.crawl(domain)
            self.redirect("/")
