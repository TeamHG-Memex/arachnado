# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

from tornado.web import Application, RequestHandler, url

from arachnado.utils import json_encode
from arachnado.spider import create_crawler
from arachnado.monitor import Monitor
from arachnado.handler_utils import ApiHandler, NoEtagsMixin

at_root = lambda *args: os.path.join(os.path.dirname(__file__), *args)


def get_application(crawler_process, debug=True):
    context = {'crawler_process': crawler_process}

    handlers = [
        url(r"/", Index, context , name="index"),
        url(r"/help", Help, context, name="help"),
        url(r"/settings", Settings, context, name="settings"),
        url(r"/crawler/start", StartCrawler, context, name="start"),
        url(r"/crawler/stop", StopCrawler, context, name="stop"),
        url(r"/crawler/pause", PauseCrawler, context, name="pause"),
        url(r"/crawler/resume", ResumeCrawler, context, name="resume"),
        url(r"/ws-updates", Monitor, context, name="ws"),
    ]
    return Application(
        handlers=handlers,
        template_path=at_root("templates"),
        compiled_template_cache=not debug,
        static_hash_cache=not debug,
        static_path=at_root("static"),
        # no_keep_alive=True,
        compress_response=True,
    )


class BaseRequestHandler(RequestHandler):

    def initialize(self, crawler_process):
        """
        :param arachnado.crawler_process.ArachnadoCrawlerProcess crawler_process: crawler process
        """
        self.crawler_process = crawler_process

    def render(self, *args, **kwargs):
        proc_stats = self.crawler_process.procmon.get_recent()
        kwargs['initial_process_stats_json'] = json_encode(proc_stats)
        return super(BaseRequestHandler, self).render(*args, **kwargs)


class Index(NoEtagsMixin, BaseRequestHandler):

    def get(self):
        jobs = self.crawler_process.jobs
        initial_data_json = json_encode({"jobs": jobs})
        return self.render("index.html", initial_data_json=initial_data_json)


class Help(BaseRequestHandler):
    def get(self):
        return self.render("help.html")


class Settings(BaseRequestHandler):
    def get(self):
        return self.render("settings.html")


class StartCrawler(ApiHandler, BaseRequestHandler):
    """
    This endpoint starts crawling for a domain.
    """
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


class _ControlJobHandler(ApiHandler, BaseRequestHandler):
    def control_job(self, job_id):
        raise NotImplementedError

    def post(self):
        if self.is_json:
            job_id = int(self.json_args['job_id'])
            self.control_job(job_id)
            return {"status": "ok"}
        else:
            job_id = int(self.get_body_argument('job_id'))
            self.control_job(job_id)
            self.redirect("/")


class StopCrawler(_ControlJobHandler):
    """ This endpoint stops a running job. """
    def control_job(self, job_id):
        self.crawler_process.stop_job(job_id)


class PauseCrawler(_ControlJobHandler):
    """ This endpoint pauses a job. """
    def control_job(self, job_id):
        self.crawler_process.pause_job(job_id)


class ResumeCrawler(_ControlJobHandler):
    """ This endpoint resumes a paused job. """
    def control_job(self, job_id):
        self.crawler_process.resume_job(job_id)
