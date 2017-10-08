from arachnado.rpc.mongotailwrapper import MongoTailStorageWrapper


class Pages(MongoTailStorageWrapper):
    storage_param_name = "pages"