#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Arachnado Crawling Server.

Usage: arachnado [options]

Options:
  --port <port>             Port to use [default: 8888]
  --host <host>             Host to bind to [default: ].
  --manhole                 Start a manhole server.
  --manhole-port <port>     Manhole server port [default: 6023]
  --manhole-host <host>     Manhole server host [default: 127.0.0.1]
  --reactor <name>          Set base event loop. Allowed values are
                            "twisted", "tornado" and "auto" [default: auto]
  --debug                   Enable debug mode.
  -L --loglevel <level>     Set log level [default: DEBUG]
  -h --help                 Show this help

"""
from __future__ import absolute_import
import logging

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


def main(port, host, start_manhole, manhole_port, manhole_host, loglevel):
    from arachnado.handlers import get_application
    from arachnado.crawler_process import ArachnadoCrawlerProcess
    from arachnado import manhole

    settings = {'LOG_LEVEL': loglevel}
    crawler_process = ArachnadoCrawlerProcess(settings)

    app = get_application(crawler_process)
    app.listen(int(port), host)

    if start_manhole:
        manhole.start(manhole_port, manhole_host, {'cp': crawler_process})

    crawler_process.start(stop_after_crawl=False)


def run():
    args = docopt(__doc__)

    if args["--reactor"] not in {'twisted', 'tornado', 'auto'}:
        raise ValueError("Invalid --reactor value: %r" % args['--reactor'])

    if args['--reactor'] == 'auto':
        # manhole doesn't work well when run on tornado event loop
        use_twisted_reactor = args['--manhole']
    else:
        use_twisted_reactor = args['--reactor'] == "twisted"

    setup_event_loop(
        use_twisted_reactor=use_twisted_reactor,
        debug=args['--debug']
    )
    main(
        port=int(args['--port']),
        host=args['--host'],
        start_manhole=args['--manhole'],
        manhole_port=int(args['--manhole-port']),
        manhole_host=args['--manhole-host'],
        loglevel=args['--loglevel'],
    )


if __name__ == "__main__":
    run()
