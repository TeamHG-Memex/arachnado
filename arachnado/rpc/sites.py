from arachnado.sitechecker import site_created, site_updated, site_deleted


class SitesRpc(object):

    def __init__(self, site_checker_crawler, **kwargs):
        self.site_checker_crawler = site_checker_crawler

    def list(self):
        return self.site_checker_crawler.storage.list()

    def post(self, site):
        self.site_checker_crawler.storage.create(site)

    def patch(self, site):
        self.site_checker_crawler.storage.update(site)

    def delete(self, site):
        self.site_checker_crawler.storage.delete(site)

    def on_open(self):
        self.site_checker_crawler.site_signals.connect(self.on_site_created, site_created)
        self.site_checker_crawler.site_signals.connect(self.on_site_updated, site_updated)
        self.site_checker_crawler.site_signals.connect(self.on_site_deleted, site_deleted)

        #self.write_event("sites:set", self.crawler.sites.values())

    def on_close(self):
        self.site_checker_crawler.site_signals.disconnect(self.on_site_created, site_created)
        self.site_checker_crawler.site_signals.disconnect(self.on_site_updated, site_updated)
        self.site_checker_crawler.site_signals.disconnect(self.on_site_deleted, site_deleted)
