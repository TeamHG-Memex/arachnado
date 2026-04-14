# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import tempfile
import logging

from tornado.web import Application, RequestHandler, url, HTTPError
# from tornado.escape import json_decode

from arachnado.utils.misc import json_encode
from arachnado.monitor import Monitor
from arachnado.handler_utils import ApiHandler, NoEtagsMixin

from arachnado.rpc.data import PagesDataRpcWebsocketHandler, JobsDataRpcWebsocketHandler

from arachnado.rpc import RpcHttpHandler
from arachnado.rpc.ws import RpcWebsocketHandler

logger = logging.getLogger(__name__)


at_root = lambda *args: os.path.join(os.path.dirname(__file__), *args)


def get_application(crawler_process, domain_crawlers,
                    site_storage, item_storage, job_storage, opts):
    context = {
        'crawler_process': crawler_process,
        'domain_crawlers': domain_crawlers,
        'job_storage': job_storage,
        'site_storage': site_storage,
        'item_storage': item_storage,
        'opts': opts,
    }
    debug = opts['arachnado']['debug']

    handlers = [
        # UI
        url(r"/", Index, context, name="index"),
        url(r"/help", Help, context, name="help"),

        # simple API used by UI
        url(r"/crawler/start", StartCrawler, context, name="start"),
        url(r"/crawler/stop", StopCrawler, context, name="stop"),
        url(r"/crawler/pause", PauseCrawler, context, name="pause"),
        url(r"/crawler/resume", ResumeCrawler, context, name="resume"),
        url(r"/crawler/status", CrawlerStatus, context, name="status"),
        url(r"/ws-updates", Monitor, context, name="ws-updates"),

        # Project upload
        url(r"/project/upload", UploadProject, context, name="upload-project"),
        url(r"/project/list", ListProjects, context, name="list-projects"),

        # RPC API
        url(r"/ws-rpc", RpcWebsocketHandler, context, name="ws-rpc"),
        url(r"/rpc", RpcHttpHandler, context, name="rpc"),
        url(r"/ws-pages-data", PagesDataRpcWebsocketHandler, context, name="ws-pages-data"),
        url(r"/ws-jobs-data", JobsDataRpcWebsocketHandler, context, name="ws-jobs-data"),
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

    def initialize(self, crawler_process, domain_crawlers,
                   site_storage, opts, **kwargs):
        """
        :param arachnado.crawler_process.ArachnadoCrawlerProcess
            crawler_process:
        """
        self.crawler_process = crawler_process
        self.domain_crawlers = domain_crawlers
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
        self.crawler = self.domain_crawlers.start(domain, args, settings)
        return bool(self.crawler)

    def post(self):
        if self.is_json:
            domain = self.json_args['domain']
            args = self.json_args.get('options', {}).get('args', {})
            settings = self.json_args.get('options', {}).get('settings', {})
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
            job_id = self.json_args['job_id']
            self.control_job(job_id)
            self.write({"status": "ok"})
        else:
            job_id = self.get_body_argument('job_id')
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
    # FIXME: does it work? Can we remove it? It is not used
    # by Arachnado UI.
    def get(self):
        crawl_ids_arg = self.get_argument('crawl_ids', '')

        if crawl_ids_arg == '':
            jobs = self.crawler_process.get_jobs()
        else:
            crawl_ids = set(crawl_ids_arg.split(','))
            jobs = [job for job in self.crawler_process.get_jobs()
                    if job['id'] in crawl_ids]

        self.write(json_encode({"jobs": jobs}))


class UploadProject(ApiHandler, BaseRequestHandler):
    """
    This endpoint handles uploading Scrapy projects.
    """
    def post(self):
        try:
            if not hasattr(self.domain_crawlers, 'project_manager'):
                raise HTTPError(500, reason="Project upload is not configured")
            
            # Get the uploaded file
            if 'project_file' not in self.request.files:
                raise HTTPError(400, reason="No file uploaded")
            
            file_info = self.request.files['project_file'][0]
            project_name = self.get_body_argument('project_name', '').strip()
            
            if not project_name:
                raise HTTPError(400, reason="Project name is required")
            
            # Validate project name (alphanumeric, underscores, hyphens only)
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', project_name):
                raise HTTPError(400, reason="Invalid project name. Use only letters, numbers, underscores, and hyphens.")
            
            # Save uploaded file to a temporary location
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.archive')
            try:
                temp_file.write(file_info['body'])
                temp_file.close()
                
                # Extract the project
                project_path = self.domain_crawlers.project_manager.extract_project(
                    temp_file.name, project_name
                )
                
                # Get spider packages from the project
                spider_packages = self.domain_crawlers.project_manager.get_project_spider_packages(project_name)
                
                # Update domain_crawlers with new spider packages
                self.domain_crawlers.add_spider_packages(spider_packages)
                
                logger.info("Uploaded project '%s' with spider packages: %s", project_name, spider_packages)
                
                if self.is_json:
                    self.write({
                        "status": "ok",
                        "project_name": project_name,
                        "spider_packages": spider_packages
                    })
                else:
                    self.redirect("/")
                    
            finally:
                # Clean up temp file
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                    
        except HTTPError:
            raise
        except Exception as e:
            logger.error("Error uploading project: %s", e, exc_info=True)
            if self.is_json:
                self.set_status(500)
                self.write({"status": "error", "message": str(e)})
            else:
                raise HTTPError(500, reason=str(e))


class ListProjects(ApiHandler, BaseRequestHandler):
    """
    This endpoint lists uploaded projects.
    """
    def get(self):
        try:
            if not hasattr(self.domain_crawlers, 'project_manager'):
                projects = []
            else:
                projects = self.domain_crawlers.project_manager.list_projects()
            
            self.write(json_encode({"projects": projects}))
        except Exception as e:
            logger.error("Error listing projects: %s", e, exc_info=True)
            self.set_status(500)
            self.write({"status": "error", "message": str(e)})
