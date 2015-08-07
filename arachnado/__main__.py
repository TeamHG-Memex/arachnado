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
  -h --help                 Show this help

"""
from __future__ import absolute_import
import os
import sys
import logging

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
    from arachnado import manhole

    settings = {'LOG_LEVEL': loglevel}
    crawler_process = ArachnadoCrawlerProcess(settings)

    app = get_application(crawler_process, opts)
    app.listen(int(port), host)
    logger.info("Arachnado v%s is started on %s:%s" % (__version__, host, port))

    if start_manhole:
        manhole.start(manhole_port, manhole_host, {'cp': crawler_process})
        logger.info("Manhole server is started on %s:%s" % (
            manhole_host, manhole_port))

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
    ensure_bool(opts, 'arachnado.storage', 'enabled')
    ensure_bool(opts, 'arachnado.manhole', 'enabled')
    return opts


def run():
    args = docopt(__doc__, version=__version__)
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
