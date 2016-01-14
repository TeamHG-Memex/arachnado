#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Arachnado Crawling Server.

Usage:
    arachnado [options]
    arachnado show-settings [options]

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
  -h --help                 Show this help

"""
from __future__ import absolute_import
import os
import sys
import logging
from os import getenv

from docopt import docopt
from tornado.ioloop import IOLoop
import tornado.platform.twisted


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


def main(port, host, start_manhole, manhole_port, manhole_host, loglevel,
         opts):
    from arachnado.handlers import get_application
    from arachnado.crawler_process import ArachnadoCrawlerProcess
    from arachnado.site_checker import get_site_checker_crawler
    from arachnado.storages.mongo import MongoStorage
    from arachnado.storages.mongotail import MongoTailStorage
    from arachnado.cron import Cron
    from arachnado import manhole

    settings = {'LOG_LEVEL': loglevel}
    crawler_process = ArachnadoCrawlerProcess(settings, opts)
    job_storage = MongoTailStorage(
        getenv(opts['arachnado.jobs']['mongo_uri_env']) or
        opts['arachnado.jobs']['mongo_uri'],
        cache=True,
    )
    site_storage = MongoStorage(
        getenv(opts['arachnado.sites']['mongo_uri_env']) or
        opts['arachnado.sites']['mongo_uri'],
        cache=True,
    )
    page_storage = MongoTailStorage(
        getenv(opts['arachnado.mongo_export']['items_mongo_uri_env']) or
        opts['arachnado.mongo_export']['items_mongo_uri'],
    )
    site_checker_crawler = get_site_checker_crawler(site_storage)
    crawler_process.crawl(site_checker_crawler)

    cron = Cron(crawler_process, site_storage)
    cron.start()

    app = get_application(crawler_process, site_storage, page_storage, job_storage, opts)
    app.listen(int(port), host)

    if start_manhole:
        manhole.start(manhole_port, manhole_host, {'cp': crawler_process})

    crawler_process.start(stop_after_crawl=False)


def _settings(args):
    from arachnado.options import load_settings, ensure_bool

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
    opts = load_settings(config_files, overrides)
    ensure_bool(opts, 'arachnado', 'debug')
    ensure_bool(opts, 'arachnado.mongo_export', 'enabled')
    ensure_bool(opts, 'arachnado.manhole', 'enabled')
    return opts


def run():
    args = docopt(__doc__)
    opts = _settings(args)

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
