JSON RPC API
============

Arachnado provides JSON-RPC_ API for working with jobs and crawled items
(pages). The API works over WebSocket transport.

JSON-RPC requests have the following format::

    {
        "jsonrpc": "2.0",

        # pass unique request id here; this id will be included in response
        "id": 362810,

        # command to execute
        "method": "<method name>",
        "params": {"name": "value"},
    }

JSON-RPC responses::

    {
        "jsonrpc": "2.0",

        # id of the request
        "id": 362810,

        # what command returns
        "result": ...
    }

Working with jobs and pages
---------------------------

JSON-RPC API allows to

* get information about scraping jobs;
* start new crawls;
* subscripbe to crawled pages;
* subscribe to job updates.

jobs.subscribe
    Get information about jobs and subscribe for new jobs.

    Parameters:

    * last_id - optional, ObjectID value of a last previously seen job;
      When passed, only new job data is returned;
    * query - optional, MongoDB query;
    * fields - optional, set of fields to return.

pages.subscribe
    Get crawled pages and subscribe for new pages.

    Parameters:

    * last_id - optional, ObjectID value of a last previously seen page.
      When passed, only new job data is returned;
    * query - optional, MongoDB query;
    * fields - optional, set of fields to return.


New API
=======

Working with jobs
-----------------

Open a websocket connection to ``/ws-jobs-data`` in order to use
jobs JSON-RPC API for scraping jobs.

subscribe_to_jobs
    Get information about jobs and subscribe for new jobs.
    Parameters:

    * include - an array of regexes which should match URLs to include;
    * exclude - an array of regexes; URLs matched by these regexes are excluded
      from the result;
    * update_delay - (opional) int, a minimum number of ms between websocket messages. If this parameter set then Arachnado will aggregate job statistics;
    * last_job_id - optional, ObjectID value of a last previously seen job.
      When passed, only new job data is returned.


    Response contains subscription ID in ``['result']['id']`` field::

        {
            'id': '<request id>',
            'jsonrpc': '2.0',
            'result': {'datatype': 'job_subscription_id', 'id': '0'}
        }

    Use this ID to cancel the subscription.

    After the subscription Arachnado will start to send information
    about new jobs. Messages look like this::

        {
             '_id': '574718bba7a4edb9b026f248',
             'finished_at': '2016-05-26 16:03:17',
             'id': '97ca610fa8c347dbafeca9fcd02213dd',
             'options': {
                         'args': {},
                         'crawl_id': '97ca610fa8c347dbafeca9fcd02213dd',
                         'domain': 'scrapy.org',
                         'settings': {}
                         },
             'spider': 'generic',
             'started_at': '2016-05-26 16:03:16',
             'stats': {...},
             'status': 'finished'
        }

cancel_subscription
    Stop receiving updates about jobs. Parameters:

    * subscription_id


set_max_message_size
    Set maximum message size in bytes for websockets channel.
    Messages larger than specified limit are dropped.
    Default value is 2**20.
    To disable this check set max size to zero.
    Parameters:
    * max_size - maximum message size in bytes.

    Response returns result(true/false) at result field::


         {
            "id": '<request id>',
            "result": true,
            "jsonrpc": "2.0"
         }


Working with pages (crawled items)
----------------------------------

Open a websocket connection to ``/ws-pages-data`` in order to use
jobs JSON-RPC API for scraping jobs.

subscribe_to_pages
    Get crawled pages(items) for specific urls.
    Url values are used as regex without any modifications at Arachnado side.
    Allows to get all pages or only crawled since last update.
    Search function uses job start urls, not page urls.
    For example, if job was started for www.mysite.com and then goes to www.example.com (by redirect, etc.),
    all its pages will be returned by www.mysite.com search query.
    To search pages by its own urls use pages.subscribe method described above.
    To get only new pages set last seen page id (from "id" field of page record) for an url.
    To get all pages set page id to None.

    Parameters:

    * urls - a dictionary of <url>:<last seen page id pairs>. Arachnado will create one subscription id for all urls;
    * url_groups - a dictionary of <url group id>: {<url>:<last seen page id pairs>}. Arachnado will create one subscription id for each url group.

    Command example::

            {
              'id': '<request id>',
              'jsonrpc': '2.0',
              'method': 'subscribe_to_pages',
              'params': {
                         'urls': {'http://example.com': None},
                         'url_groups': {
                                        'gr1': {'http://example1.com': None},
                                        'gr2': {'http://example2.com': "57863974a8cb9c15e8f3d53a"}}
                                       }
                        }
            }

    Response example for above command::

        {
            "result": {
                        "datatype": "pages_subscription_id",
                        "single_subscription_id": "112", # subscription id for http://example.com subscription
                        "id": {
                                "gr1": "113", # subscription id for http://example1.com subscription
                                "gr2": "114", # subscription id for http://example2.com subscription
                                }
                      },
            "id": '<request id>', # command request id
            "jsonrpc": "2.0"
        }

    Use these IDs to cancel subscriptions.

    After the subscription Arachnado will start to send information
    about crawled pages. Messages look like this::

        {
            "status": 200,
            "items": [],
            "_id": "57863974a8cb9c15e8f3d53a",
            "url": "http://example.com/index.php",
            "headers": {},
            "_type": "page",
            "body": ""
        }


cancel_subscription
    Stop receiving updates. Parameters:

    * subscription_id

set_max_message_size
    Set maximum message size in bytes for websockets channel.
    Messages larger than specified limit are dropped.
    Default value is 2**20.
    To disable this check set max size to zero.
    Parameters:
    * max_size - maximum message size in bytes.

    Response returns result(true/false) at result field::

        {
            "id": '<request id>',,
            "result": true,
            "jsonrpc": "2.0"
        }


.. _JSON-RPC: http://www.jsonrpc.org/specification
