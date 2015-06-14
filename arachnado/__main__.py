#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

from tornado.ioloop import IOLoop
import tornado.platform.twisted


def setup_event_loop(use_tornado, debug=True):
    if use_tornado:
        tornado.platform.twisted.install()
        IOLoop.instance().set_blocking_log_threshold(0.5)
        if debug:
            print("Using Tornado event loop as a Twisted reactor")
    else:
        tornado.platform.twisted.TwistedIOLoop().install()
        if debug:
            print("Using Twisted reactor as a Tornado event loop")


def main():
    from .handlers import get_application
    from .crawler_process import ArachnadoCrawlerProcess

    crawler_process = ArachnadoCrawlerProcess()

    app = get_application(crawler_process)
    app.listen(8888)

    crawler_process.start(stop_after_crawl=False)


def run():
    setup_event_loop(use_tornado=True, debug=True)
    main()


if __name__ == "__main__":
    run()
