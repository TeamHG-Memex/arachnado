from scrapy.utils.misc import walk_modules
from scrapy.utils.spider import iter_spider_classes


def get_spider_cls(url, spider_packages, default):
    """
    Return spider class based on provided url.

    :param url: if it looks like `spider://spidername` it tries to load spider
        named `spidername`, otherwise it returns default spider class
    :param spider_packages: a list of package names that will be searched for
        spider classes
    :param default: the class that is returned when `url` doesn't start with
        `spider://`
    """
    if url.startswith('spider://'):
        spider_name = url[len('spider://'):]
        return find_spider_cls(spider_name, spider_packages)
    return default


def find_spider_cls(spider_name, spider_packages):
    """
    Find spider class which name is equal to `spider_name` argument

    :param spider_name: spider name to look for
    :param spider_packages: a list of package names that will be searched for
        spider classes
    """
    for package_name in spider_packages:
        for module in walk_modules(package_name):
            for spider_cls in iter_spider_classes(module):
                if spider_cls.name == spider_name:
                    return spider_cls
