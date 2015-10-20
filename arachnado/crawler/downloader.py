from scrapy import signals
from scrapy.core.downloader import Downloader


class ArachnadoDownloader(Downloader):
    """A downloader that dispatches additional signals:

        - downloader_enqueued:
            when new request appears in queue

        - downloader_dequeued:
            when request is ready to download
    """
    def _enqueue_request(self, request, spider):
        dfd = super(ArachnadoDownloader, self)._enqueue_request(request,
                                                                spider)
        self.signals.send_catch_log(signals.downloader_enqueued)

        def _send_dequeued(_):
            self.signals.send_catch_log(signals.downloader_dequeued)
            return _

        dfd.addBoth(_send_dequeued)
        return dfd
