# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

from tornado.web import Application, RequestHandler, url, HTTPError
# from tornado.escape import json_decode

from arachnado.utils.misc import json_encode
from arachnado.monitor import Monitor
from arachnado.handler_utils import ApiHandler, NoEtagsMixin
from arachnado.rpc import MainRpcHttpHandler, MainRpcWebsocketHandler


at_root = lambda *args: os.path.join(os.path.dirname(__file__), *args)


def get_application(crawler_process, site_storage, page_storage, job_storage, opts):
    context = {
        'crawler_process': crawler_process,
        'job_storage': job_storage,
        'site_storage': site_storage,
        'page_storage': page_storage,
        'opts': opts,
    }
    debug = opts['arachnado']['debug']

    handlers = [
        url(r"/", Index, context, name="index"),
        url(r"/help", Help, context, name="help"),
        url(r"/crawler/start", StartCrawler, context, name="start"),
        url(r"/crawler/stop", StopCrawler, context, name="stop"),
        url(r"/crawler/pause", PauseCrawler, context, name="pause"),
        url(r"/crawler/resume", ResumeCrawler, context, name="resume"),
        url(r"/crawler/status", CrawlerStatus, context, name="status"),
        url(r"/ws-updates", Monitor, context, name="ws-updates"),
        url(r"/ws-rpc", MainRpcWebsocketHandler, context, name="ws-rpc"),
        url(r"/rpc", MainRpcHttpHandler, context, name="rpc"),
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

    def initialize(self, crawler_process, site_storage, opts, **kwargs):
        """
        :param arachnado.crawler_process.ArachnadoCrawlerProcess
            crawler_process:
        """
        self.crawler_process = crawler_process
        self.site_storage = site_storage
        self.opts = opts

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


class StartCrawler(ApiHandler, BaseRequestHandler):
    """
    This endpoint starts crawling for a domain.
    """
    def crawl(self, domain, args, settings):
        self.crawler = self.crawler_process.start_crawl(domain, args, settings)
        return bool(self.crawler)

    def post(self):
        if self.is_json:
            domain = self.json_args['domain']
            args = self.json_args.get('options', {}).get('args', {})
            settings = self.json_args.get('options', {}).get('settings', {})
            args['user_settings'] = settings
            if self.crawl(domain, args, settings):
                self.write({"status": "ok",
                            "job_id": self.crawler.spider.crawl_id})
            else:
                self.write({"status": "error"})
        else:
            domain = self.get_body_argument('domain')
            if self.crawl(domain, {}, {}):
                self.redirect("/")
            else:
                raise HTTPError(400)


class _ControlJobHandler(ApiHandler, BaseRequestHandler):
    def control_job(self, job_id, **kwargs):
        raise NotImplementedError

    def post(self):
        if self.is_json:
            job_id = int(self.json_args['job_id'])
            self.control_job(job_id)
            self.write({"status": "ok"})
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


class CrawlerStatus(BaseRequestHandler):
    """ Status for one or more jobs. """
    def get(self):
        crawl_ids_arg = self.get_argument('crawl_ids', '')

        if crawl_ids_arg == '':
            jobs = self.crawler_process.get_jobs()
        else:
            crawl_ids = set(map(int, crawl_ids_arg.split(',')))
            jobs = [job for job in self.crawler_process.get_jobs()
                    if job['id'] in crawl_ids]

        self.write(json_encode({"jobs": jobs}))
