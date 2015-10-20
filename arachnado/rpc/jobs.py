class JobsRpc(object):

    def __init__(self, handler, jobs_storage, **kwargs):
        self.handler = handler
        self.storage = jobs_storage

    def subscribe(self):
        pass

    def unsubscribe(self):
        pass

    def start(self, spider=None, args=None, settings=None):
        pass

    def stop(self, job_id):
        pass

    def pause(self, job_id):
        pass
