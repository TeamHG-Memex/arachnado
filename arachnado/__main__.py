#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from tornado.platform.twisted import TwistedIOLoop
from .handlers import get_application
from .crawler_process import ArachnadoCrawlerProcess


if __name__ == "__main__":
    TwistedIOLoop().install()
    crawler_process = ArachnadoCrawlerProcess()

    app = get_application(crawler_process)
    app.listen(8888)

    crawler_process.start(stop_after_crawl=False)
