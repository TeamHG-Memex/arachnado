# -*- coding: utf-8 -*-
from __future__ import absolute_import  
from scrapy.utils.serialize import ScrapyJSONEncoder

_encoder = ScrapyJSONEncoder(ensure_ascii=False)


def json_encode(obj):
    """
    Encode a Python object to JSON.
    Unlike standard json.dumps, datetime.datetime objects are supported.
    """
    return _encoder.encode(obj)


def decorate_methods(method_names, decorator):
    """ Class decorator which applies a decorator to all specified methods """
    def _decorator(cls):
        for name in method_names:
            wrapped = decorator(getattr(cls, name))
            setattr(cls, name, wrapped)
        return cls
    return _decorator
