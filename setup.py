#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from setuptools import setup, find_packages

with open("README.rst") as f:
    long_description = f.read()

with open("CHANGES.rst") as f:
    long_description += "\n\n" + f.read()


def get_version():
    fn = os.path.join(os.path.dirname(__file__), "arachnado", "__init__.py")
    with open(fn) as f:
        return re.findall("__version__ = '([\d\.]+)'", f.read())[0]


setup(
    name='arachnado',
    version=get_version(),
    url='https://github.com/TeamHG-Memex/arachnado',
    description='Scrapy-based Web Crawler with an UI',
    long_description=long_description,
    author='Mikhail Korobov',
    author_email='kmike84@gmail.com',
    license='MIT',
    packages=find_packages(),
    package_data={
        'arachnado': [
            "config/*.conf",
            "templates/*.html",
            "static/css/*.css",
            
            "static/build/*.css",
            "static/build/*.js",

            "static/js/*.jsx",
            "static/js/*.js",
            "static/js/components/*.jsx",
            "static/js/components/*.js",
            "static/js/pages/*.jsx",
            "static/js/pages/*.js",
            "static/js/stores/*.jsx",
            "static/js/stores/*.js",
            "static/js/utils/*.jsx",
            "static/js/utils/*.js",
        ]
    },

    zip_safe=False,
    entry_points={
        'console_scripts': ['arachnado = arachnado.__main__:run']
    },
    classifiers=[
        'Framework :: Scrapy',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'scrapy >= 1.1.0',
        'Twisted >= 16',
        'psutil >= 2.2',
        'tornado >= 4.2, < 4.3',
        'docopt >= 0.6',
        'service_identity',
        'motor >= 0.6.2',
        'json-rpc >= 1.10',
        'autologin-middleware >= 0.1.1',
        'six',
        'croniter >= 0.3.12',
    ],
    extras_require={
        'mongo': [],   # backwards compatibility
        'extras': ['autopager >= 0.2'],
    }
)
