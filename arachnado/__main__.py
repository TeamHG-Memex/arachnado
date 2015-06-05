#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import  
from .handlers import get_application
from .crawler_process import TornadoCrawlerProcess


if __name__ == "__main__":
    crawler_process = TornadoCrawlerProcess()

    app = get_application(crawler_process)
    app.listen(8888)

    crawler_process.start(stop_after_crawl=False)
