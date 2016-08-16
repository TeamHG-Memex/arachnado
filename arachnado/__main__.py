#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Arachnado Crawling Server.

Usage:
    arachnado [options]
    arachnado show-settings

Options:

  -p --port <port>          Port to use.
  -h --host <host>          Host to bind.
  -c --config <path>        Path to config file.
  -L --loglevel <level>     Set log level.
  --manhole                 Start a manhole server.
  --manhole-port <port>     Manhole server port.
  --manhole-host <host>     Manhole server host.
  --reactor <name>          Set base event loop. Allowed values are
                            "twisted", "tornado" and "auto".
  --debug                   Enable debug mode.
  --version                 Show version information
  --help                    Show this help

"""
from __future__ import absolute_import
import os
import re
import sys
import logging
from os import getenv

from docopt import docopt
from tornado.ioloop import IOLoop
import tornado.platform.twisted

from arachnado import __version__


logger = logging.getLogger('arachnado')


def setup_event_loop(use_twisted_reactor, debug=True):
    if use_twisted_reactor:
        tornado.platform.twisted.TwistedIOLoop().install()
        if debug:
            print("Using Twisted reactor as a Tornado event loop")
    else:
        tornado.platform.twisted.install()
        IOLoop.instance().set_blocking_log_threshold(0.5)
        if debug:
            print("Using Tornado event loop as a Twisted reactor")


def main(port, host, start_manhole, manhole_port, manhole_host, loglevel, opts):
    from arachnado.handlers import get_application
    from arachnado.crawler_process import ArachnadoCrawlerProcess
    from arachnado.site_checker import get_site_checker_crawler
    from arachnado.storages.mongo import MongoStorage
    from arachnado.storages.mongotail import MongoTailStorage
    from arachnado.domain_crawlers import DomainCrawlers
    from arachnado.cron import Cron

    settings = {
        'LOG_LEVEL': loglevel,
    }

    # mongo export options
    storage_opts = opts['arachnado.storage']
    assert storage_opts['enabled'], "Storage can't be turned off"

    items_uri = _getval(storage_opts, 'items_uri_env', 'items_uri')
    jobs_uri = _getval(storage_opts, 'jobs_uri_env', 'jobs_uri')
    sites_uri = _getval(storage_opts, 'sites_uri_env', 'sites_uri')

    scrapy_opts = opts['arachnado.scrapy']
    settings.update({k: v for k, v in scrapy_opts.items() if k.isupper()})

    settings.update({
        'MONGO_EXPORT_ENABLED': storage_opts['enabled'],
        'MONGO_EXPORT_JOBS_URI': jobs_uri,
        'MONGO_EXPORT_ITEMS_URI': items_uri,
    })

    job_storage = MongoTailStorage(jobs_uri, cache=True)
    job_storage.ensure_index("urls")
    site_storage = MongoStorage(sites_uri, cache=True)
    item_storage = MongoTailStorage(items_uri)
    item_storage.ensure_index("url")
    item_storage.ensure_index("_job_id")

    crawler_process = ArachnadoCrawlerProcess(settings)

    site_checker_crawler = get_site_checker_crawler(site_storage)
    crawler_process.crawl(site_checker_crawler)

    spider_packages = scrapy_opts['spider_packages']
    default_spider_name = scrapy_opts['default_spider_name']
    domain_crawlers = DomainCrawlers(
        crawler_process=crawler_process,
        spider_packages=_parse_spider_packages(spider_packages),
        default_spider_name=default_spider_name,
        settings=settings
    )
    domain_crawlers.resume(job_storage)

    cron = Cron(domain_crawlers, site_storage)
    cron.start()

    app = get_application(crawler_process, domain_crawlers,
                          site_storage, item_storage, job_storage, opts)
    app.listen(int(port), host)
    logger.info("Arachnado v%s is started on %s:%s" % (__version__, host, port))

    if start_manhole:
        from arachnado import manhole
        manhole.start(manhole_port, manhole_host, {'cp': crawler_process})
        logger.info("Manhole server is started on %s:%s" % (
            manhole_host, manhole_port))

    crawler_process.start(stop_after_crawl=False)


def _getval(opts, env_key, key):
    return getenv(opts[env_key]) or opts[key]


def _parse_spider_packages(spider_packages):
    """
    >>> _parse_spider_packages("mypackage.spiders package2  package3  ")
    ['mypackage.spiders', 'package2', 'package3']
    """
    return [name for name in re.split('\s+', spider_packages) if name]


def _get_opts(args):
    """ Combine options from config files and command-line arguments """
    from arachnado.config import load_config, ensure_bool

    if args['--config']:
        path = os.path.expanduser(args['--config'])
        assert os.path.exists(path)
        config_files = [path]
    else:
        config_files = []

    def _overrides(section, mapping):
        return [
            [section, ini_key, args[args_key]]
            for ini_key, args_key in mapping.items()
        ]

    overrides = _overrides('arachnado', {
        'port': '--port',
        'host': '--host',
        'reactor': '--reactor',
        'loglevel': '--loglevel',
        'debug': '--debug',
    }) + _overrides('arachnado.manhole', {
        'enabled': '--manhole',
        'port': '--manhole-port',
        'host': '--manhole-host',
    })
    opts = load_config(config_files, overrides)
    ensure_bool(opts, 'arachnado', 'debug')
    ensure_bool(opts, 'arachnado.storage', 'enabled')
    ensure_bool(opts, 'arachnado.manhole', 'enabled')
    return opts


def run():
    args = docopt(__doc__, version=__version__)
    opts = _get_opts(args)

    if args['show-settings']:
        from pprint import pprint
        pprint(opts)
        sys.exit(1)

    _reactor = opts['arachnado']['reactor']
    if _reactor not in {'twisted', 'tornado', 'auto'}:
        raise ValueError("Invalid 'reactor': %r" % _reactor)

    if _reactor == 'auto':
        # manhole doesn't work well when run on tornado event loop
        use_twisted_reactor = opts['arachnado.manhole']['enabled']
    else:
        use_twisted_reactor = _reactor == "twisted"

    setup_event_loop(
        use_twisted_reactor=use_twisted_reactor,
        debug=opts['arachnado']['debug']
    )
    main(
        port=int(opts['arachnado']['port']),
        host=opts['arachnado']['host'],
        start_manhole=opts['arachnado.manhole']['enabled'],
        manhole_port=int(opts['arachnado.manhole']['port']),
        manhole_host=opts['arachnado.manhole']['host'],
        loglevel=opts['arachnado']['loglevel'],
        opts=opts,
    )


if __name__ == "__main__":
    run()
