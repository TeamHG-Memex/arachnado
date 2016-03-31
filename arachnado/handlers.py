# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import re

from scrapy.utils.misc import walk_modules
from scrapy.utils.spider import iter_spider_classes
from tornado.web import Application, RequestHandler, url, HTTPError

from arachnado.utils import json_encode
from arachnado.spider import create_crawler, CrawlWebsiteSpider
from arachnado.monitor import Monitor
from arachnado.handler_utils import ApiHandler, NoEtagsMixin

at_root = lambda *args: os.path.join(os.path.dirname(__file__), *args)


def get_application(crawler_process, opts):
    context = {
        'crawler_process': crawler_process,
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


def get_spider_cls(url, spider_packages,
                   default=CrawlWebsiteSpider):
    """
    Return spider class based on provided url.

    :param url: if it looks like `spider://spidername` it tries to load spider
        named `spidername`, otherwise it returns default spider class
    :param spider_packages: a list of package names that will be searched for
        spider classes
    :param default: the class that is returned when `url` doesn't start with
        `spider://`
    """
    if url.startswith('spider://'):
        spider_name = url[len('spider://'):]
        return find_spider_cls(spider_name, spider_packages)
    return default


def find_spider_cls(spider_name, spider_packages):
    """
    Find spider class which name is equal to `spider_name` argument

    :param spider_name: spider name to look for
    :param spider_packages: a list of package names that will be searched for
        spider classes
    """
    for package_name in spider_packages:
        for module in walk_modules(package_name):
            for spider_cls in iter_spider_classes(module):
                if spider_cls.name == spider_name:
                    return spider_cls


def set_spider_class_args(spider_cls, **kwargs):
    """ Creates new spider class based on given spider class to keep the
    original spider class consistent.

    :param spider_cls: Original spider class
    :param kwargs: Custom spider attributed to be set for this particular crawl
    """
    if kwargs:
        return type(
            '{}Customized'.format(spider_cls.__name__), (spider_cls,), kwargs)
    return spider_cls


class BaseRequestHandler(RequestHandler):

    def initialize(self, crawler_process, opts):
        """
        :param arachnado.crawler_process.ArachnadoCrawlerProcess
            crawler_process:
        """
        self.crawler_process = crawler_process
        self.opts = opts

    def render(self, *args, **kwargs):
        proc_stats = self.crawler_process.procmon.get_recent()
        kwargs['initial_process_stats_json'] = json_encode(proc_stats)
        return super(BaseRequestHandler, self).render(*args, **kwargs)

    def get_custom_spider_arguments(self, ignore=None):
        """ Returns custom spider arguments embedded in request

        :param ignore: List of arguments to be ignored. Defaults to 'domain'.
        """
        ignore = ignore or ['domain']
        if self.json_args:
            args = self.json_args
            getter = self.json_args.get
        else:
            content_type = self.request.headers.get('Content-Type', '').lower()
            if 'x-www-form-urlencoded' in content_type:
                args = self.request.body_arguments
                getter = self.get_body_argument
            else:
                args = self.request.query_arguments
                getter = self.get_query_argument
        return {arg: getter(arg) for arg in args if arg not in ignore}


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
    def crawl(self, domain, **kwargs):
        storage_opts = self.opts['arachnado.storage']
        settings = {
            'MOTOR_PIPELINE_ENABLED': storage_opts['enabled'],
            'MOTOR_PIPELINE_DB_NAME': storage_opts['db_name'],
            'MOTOR_PIPELINE_DB': storage_opts['db_name'],
            'MOTOR_PIPELINE_URI': storage_opts['uri'],
        }
        spider_cls = get_spider_cls(domain, self._get_spider_package_names())

        if spider_cls is not None:
            spider_cls = set_spider_class_args(spider_cls, **kwargs)
            self.crawler = create_crawler(settings, spider_cls=spider_cls)
            self.crawler_process.crawl(self.crawler, domain=domain)
            return True
        return False

    def post(self):
        spider_args = self.get_custom_spider_arguments()
        if self.is_json:
            domain = self.json_args['domain']
            if self.crawl(domain, **spider_args):
                self.write({"status": "ok",
                            "job_id": self.crawler.spider.crawl_id})
            else:
                self.write({"status": "error"})
        else:
            domain = self.get_body_argument('domain')
            if self.crawl(domain, **spider_args):
                self.redirect("/")
            else:
                raise HTTPError(400)

    def _get_spider_package_names(self):
        return [name for name in re.split(
            '\s+', self.opts['arachnado.scrapy']['spider_packages']
        ) if name]


class _ControlJobHandler(ApiHandler, BaseRequestHandler):
    def control_job(self, job_id):
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
