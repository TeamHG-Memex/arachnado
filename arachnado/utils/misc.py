from __future__ import absolute_import
import urlparse

from scrapy.utils.serialize import ScrapyJSONEncoder
from bson.objectid import ObjectId

MB = 1024 * 1024

# XXX: this is copy-pasted to make motor_exporter independent


class JSONEncoder(ScrapyJSONEncoder):

    def __init__(self, *args, **kwargs):
        kwargs['ensure_ascii'] = False
        super(JSONEncoder, self).__init__(*args, **kwargs)

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super(JSONEncoder, self).default(o)

_encoder = JSONEncoder()


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
