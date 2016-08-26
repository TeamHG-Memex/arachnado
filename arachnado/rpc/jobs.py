from arachnado.rpc.mongotailwrapper import MongoTailStorageWrapper


class Jobs(MongoTailStorageWrapper):
    storage_param_name = "jobs"