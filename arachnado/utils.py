# -*- coding: utf-8 -*-
from __future__ import absolute_import
import urlparse
from scrapy.utils.serialize import ScrapyJSONEncoder

MB = 1024*1024


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


def add_scheme_if_missing(url):
    """
    >>> add_scheme_if_missing("example.com/foo")
    'http://example.com/foo'
    >>> add_scheme_if_missing("https://example.com/foo")
    'https://example.com/foo'
    >>> add_scheme_if_missing("//example.com/foo")
    'http://example.com/foo'
    """
    if url.startswith("//"):
        url = "http:" + url
    if "://" not in url:
        url = "http://" + url
    return url


def get_netloc(url):
    """
    >>> get_netloc("example.org/")
    'example.org'
    >>> get_netloc("http://example.org/foo")
    'example.org'
    >>> get_netloc("http://blog.example.org/foo")
    'blog.example.org'
    """
    return urlparse.urlparse(add_scheme_if_missing(url)).netloc
